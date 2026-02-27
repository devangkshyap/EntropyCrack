const passwordInput = document.getElementById('password');
const strengthBar = document.getElementById('strength-bar');
const strengthLabel = document.getElementById('strength-label');
const feedbackEl = document.getElementById('feedback');
const analyzeBtn = document.getElementById('analyze-btn');
const entropyValue = document.getElementById('entropy-value');
const breachStatus = document.getElementById('breach-status');

const dictStatus = document.getElementById('dict-status');
const dictMeta = document.getElementById('dict-meta');
const bruteStatus = document.getElementById('brute-status');
const bruteMeta = document.getElementById('brute-meta');
const etaEl = document.getElementById('eta');
const hashesEl = document.getElementById('hashes');
const recsEl = document.getElementById('recs');

// Generator elements
const genLengthSlider = document.getElementById('gen-length');
const lengthDisplay = document.getElementById('length-display');
const genUpper = document.getElementById('gen-upper');
const genLower = document.getElementById('gen-lower');
const genDigits = document.getElementById('gen-digits');
const genSpecial = document.getElementById('gen-special');
const genMemorable = document.getElementById('gen-memorable');
const generatedPassword = document.getElementById('generated-password');
const generateBtn = document.getElementById('generate-btn');
const copyBtn = document.getElementById('copy-btn');
const genStats = document.getElementById('gen-stats');
const genScore = document.getElementById('gen-score');
const genEntropy = document.getElementById('gen-entropy');
const keywordSeed = document.getElementById('keyword-seed');
const keywordMinLength = document.getElementById('keyword-min-length');
const keywordOutput = document.getElementById('keyword-password-output');
const keywordGenerateBtn = document.getElementById('keyword-generate-btn');
const keywordCopyBtn = document.getElementById('keyword-copy-btn');
const keywordStats = document.getElementById('keyword-stats');
const keywordScore = document.getElementById('keyword-score');
const keywordEntropy = document.getElementById('keyword-entropy');

// Comparison elements
const comparePw1 = document.getElementById('compare-pw1');
const comparePw2 = document.getElementById('compare-pw2');
const compareBtn = document.getElementById('compare-btn');
const comparisonResults = document.getElementById('comparison-results');
const compareStats1 = document.getElementById('compare-stats1');
const compareStats2 = document.getElementById('compare-stats2');
const compareWinner = document.getElementById('compare-winner');

// History elements
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history-btn');

// Breach checker elements
const breachPassword = document.getElementById('breach-password');
const breachCheckBtn = document.getElementById('breach-check-btn');
const breachClearBtn = document.getElementById('breach-clear-btn');
const breachResults = document.getElementById('breach-results');
const breachResultStatus = document.getElementById('breach-result-status');
const breachResultMessage = document.getElementById('breach-result-message');
const breachSeverityBadge = document.getElementById('breach-severity-badge');
const breachIcon = document.getElementById('breach-icon');
const breachResultCard = document.getElementById('breach-result-card');



function localStrengthScore(pw) {
  let score = 0;
  const lengthScore = Math.min(pw.length * 4, 30);
  const upper = /[A-Z]/.test(pw);
  const lower = /[a-z]/.test(pw);
  const digit = /[0-9]/.test(pw);
  const special = /[^A-Za-z0-9]/.test(pw);
  const variety = [upper, lower, digit, special].filter(Boolean).length >= 3 ? 10 : 0;
  const commonPattern = /(password|123456|qwerty|letmein|admin)/i.test(pw) ? -20 : 0;
  score = lengthScore + (upper ? 10 : 0) + (lower ? 10 : 0) + (digit ? 15 : 0) + (special ? 15 : 0) + variety + commonPattern;
  score = Math.max(0, Math.min(100, score));
  return score;
}

function labelForScore(score) {
  if (score < 40) return 'Weak';
  if (score < 70) return 'Medium';
  return 'Strong';
}

function updateMeter(score) {
  strengthBar.style.width = `${score}%`;
  strengthLabel.textContent = `${labelForScore(score)} (${score}%)`;
}

function showFeedback(items) {
  feedbackEl.innerHTML = '';
  items.forEach((text) => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.textContent = text;
    feedbackEl.appendChild(chip);
  });
}

passwordInput.addEventListener('input', () => {
  const score = localStrengthScore(passwordInput.value);
  updateMeter(score);
});

async function analyzePassword() {
  const password = passwordInput.value;
  if (!password) {
    showFeedback(['Enter a password to analyze.']);
    updateMeter(0);
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = 'Analyzing...';
  
  // Add running animation to the cracking panel
  const crackingPanel = document.getElementById('cracking');
  if (crackingPanel) {
    crackingPanel.classList.add('running');
  }

  try {
    const analyzeRes = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    const analyzeData = await analyzeRes.json();
    if (!analyzeRes.ok) throw new Error(analyzeData.error || 'Analyze failed');

    updateMeter(analyzeData.score);
    strengthLabel.textContent = `${analyzeData.label} (${analyzeData.score}%)`;
    showFeedback(analyzeData.feedback || []);
    
    // Display entropy
    if (analyzeData.entropy !== undefined) {
      entropyValue.textContent = `${analyzeData.entropy} bits`;
    }
    
    // Display breach check
    if (analyzeData.leaked_check) {
      const leak = analyzeData.leaked_check;
      breachStatus.textContent = leak.is_leaked ? '⚠️ Found in breaches' : '✓ Not found';
      breachStatus.style.color = leak.is_leaked ? '#ff5f6d' : '#39d98a';
    }

    const crackRes = await fetch('/crack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    const crackData = await crackRes.json();
    if (!crackRes.ok) throw new Error(crackData.error || 'Crack failed');

    renderCrackResults(crackData);
    
    // Refresh history after analysis
    loadHistory();
  } catch (err) {
    showFeedback([err.message]);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Password';
    
    // Remove running animation after complete
    if (crackingPanel) {
      crackingPanel.classList.remove('running');
    }
  }
}

function renderCrackResults(data) {
  const dict = data.results?.find((r) => r.attack.includes('Dictionary'));
  const brute = data.results?.find((r) => r.attack.includes('Brute'));

  if (dict) {
    dictStatus.textContent = dict.success ? 'Success' : 'Failed';
    dictStatus.style.color = dict.success ? '#39d98a' : '#ff5f6d';
    dictMeta.textContent = `${dict.attempts || 0} guesses • ${dict.time_taken?.toFixed(3) || 0}s` + (dict.candidate ? ` • matched "${dict.candidate}"` : '');
  }

  if (brute) {
    bruteStatus.textContent = brute.success ? 'Success' : 'Stopped';
    bruteStatus.style.color = brute.success ? '#39d98a' : '#ff7a59';
    const stopped = brute.stopped ? ` • ${brute.stopped}` : '';
    bruteMeta.textContent = `${brute.attempts || 0} guesses • ${brute.time_taken?.toFixed(3) || 0}s${stopped}`;
  }

  etaEl.textContent = data.time_to_crack_estimate || 'n/a';

  if (data.hashes) {
    hashesEl.innerHTML = `<span class="meta-row" style="word-break: break-all;">SHA-256:<br>${data.hashes.sha256}</span><br><span class="meta-row" style="word-break: break-all;">bcrypt:<br>${data.hashes.bcrypt}</span>`;
  }

  recsEl.innerHTML = '';
  (data.recommendations || []).forEach((rec) => {
    const pill = document.createElement('div');
    pill.className = 'pill';
    pill.textContent = rec;
    recsEl.appendChild(pill);
  });
}

analyzeBtn.addEventListener('click', analyzePassword);

// Password Generator Functions
genLengthSlider.addEventListener('input', () => {
  lengthDisplay.textContent = genLengthSlider.value;
});

async function generatePassword() {
  const length = parseInt(genLengthSlider.value);
  const useUpper = genUpper.checked;
  const useLower = genLower.checked;
  const useDigits = genDigits.checked;
  const useSpecial = genSpecial.checked;
  const memorable = genMemorable.checked;

  generateBtn.disabled = true;
  generateBtn.textContent = 'Generating...';

  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ length, use_upper: useUpper, use_lower: useLower, use_digits: useDigits, use_special: useSpecial, memorable }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Generation failed');

    generatedPassword.value = data.password;
    genScore.textContent = `${data.label} (${data.score}%)`;
    genEntropy.textContent = data.entropy;
    genStats.style.display = 'flex';
    copyBtn.style.display = 'inline-block';
  } catch (err) {
    alert(err.message);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Password';
  }
}

generateBtn.addEventListener('click', generatePassword);

async function generateKeywordPassword() {
  const keyword = keywordSeed.value.trim();
  const minLength = parseInt(keywordMinLength.value) || 12;

  if (!keyword) {
    alert('Please enter a keyword');
    return;
  }

  keywordGenerateBtn.disabled = true;
  keywordGenerateBtn.textContent = 'Generating...';

  try {
    const res = await fetch('/generate/related', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, min_length: minLength })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Generation failed');

    keywordOutput.value = data.password;
    keywordScore.textContent = `${data.label} (${data.score}%)`;
    keywordEntropy.textContent = data.entropy;
    keywordStats.style.display = 'flex';
    keywordCopyBtn.style.display = 'inline-block';
  } catch (err) {
    alert(err.message);
  } finally {
    keywordGenerateBtn.disabled = false;
    keywordGenerateBtn.textContent = 'Strengthen Keyword';
  }
}

keywordGenerateBtn.addEventListener('click', generateKeywordPassword);

copyBtn.addEventListener('click', () => {
  generatedPassword.select();
  document.execCommand('copy');
  const originalText = copyBtn.textContent;
  copyBtn.textContent = 'Copied!';
  setTimeout(() => {
    copyBtn.textContent = originalText;
  }, 2000);
});

keywordCopyBtn.addEventListener('click', () => {
  keywordOutput.select();
  document.execCommand('copy');
  const originalText = keywordCopyBtn.textContent;
  keywordCopyBtn.textContent = 'Copied!';
  setTimeout(() => {
    keywordCopyBtn.textContent = originalText;
  }, 2000);
});

// Password Comparison Functions
async function comparePasswords() {
  const password1 = comparePw1.value;
  const password2 = comparePw2.value;

  if (!password1 || !password2) {
    alert('Please enter both passwords');
    return;
  }

  compareBtn.disabled = true;
  compareBtn.textContent = 'Comparing...';

  try {
    const res = await fetch('/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password1, password2 }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Comparison failed');

    displayComparison(data);
  } catch (err) {
    alert(err.message);
  } finally {
    compareBtn.disabled = false;
    compareBtn.textContent = 'Compare Passwords';
  }
}

function displayComparison(data) {
  const pw1 = data.password1;
  const pw2 = data.password2;

  compareStats1.innerHTML = `
    <p><strong>Score:</strong> ${pw1.score}% (${pw1.label})</p>
    <p><strong>Entropy:</strong> ${pw1.entropy} bits</p>
    <p><strong>Length:</strong> ${pw1.length} chars</p>
    <p><strong>Leaked:</strong> ${pw1.leaked ? '⚠️ Yes' : '✓ No'}</p>
  `;

  compareStats2.innerHTML = `
    <p><strong>Score:</strong> ${pw2.score}% (${pw2.label})</p>
    <p><strong>Entropy:</strong> ${pw2.entropy} bits</p>
    <p><strong>Length:</strong> ${pw2.length} chars</p>
    <p><strong>Leaked:</strong> ${pw2.leaked ? '⚠️ Yes' : '✓ No'}</p>
  `;

  comparisonResults.style.display = 'grid';

  if (data.winner === 'tie') {
    compareWinner.innerHTML = '<p style="color:#ffa500;"><strong>🤝 Both passwords are equally strong!</strong></p>';
  } else {
    const winnerNum = data.winner === 'password1' ? '1' : '2';
    compareWinner.innerHTML = `<p style="color:#39d98a;"><strong>🏆 Password ${winnerNum} is stronger!</strong></p>`;
  }
}

compareBtn.addEventListener('click', comparePasswords);

// History Functions
async function loadHistory() {
  try {
    const res = await fetch('/history');
    const data = await res.json();
    displayHistory(data.history || []);
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

function displayHistory(history) {
  if (history.length === 0) {
    historyList.innerHTML = '<p class="hint">No history yet. Analyze a password to see it here.</p>';
    return;
  }

  historyList.innerHTML = history.map((entry, index) => `
    <div class="history-item">
      <span class="history-badge">${entry.label}</span>
      <span>Score: ${entry.score}%</span>
      <span>Entropy: ${entry.entropy} bits</span>
      <span>Length: ${entry.length}</span>
      <span class="history-time">${new Date(entry.timestamp).toLocaleString()}</span>
    </div>
  `).join('');
}

async function clearHistory() {
  try {
    const res = await fetch('/history/clear', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      loadHistory();
    }
  } catch (err) {
    alert('Failed to clear history');
  }
}

clearHistoryBtn.addEventListener('click', clearHistory);

// ===== Quiz Functionality =====
let quizData = [];
let currentQuestion = 0;
let quizScore = 0;

document.getElementById('start-quiz-btn').addEventListener('click', async () => {
  try {
    const res = await fetch('/quiz/generate', { method: 'POST' });
    const data = await res.json();
    quizData = data.questions;
    currentQuestion = 0;
    quizScore = 0;
    document.getElementById('quiz-container').style.display = 'block';
    showQuestion();
  } catch (err) {
    alert('Failed to load quiz');
  }
});

function showQuestion() {
  if (currentQuestion >= quizData.length) {
    document.getElementById('quiz-question').innerHTML = `<h3>Quiz Complete!</h3>`;
    document.getElementById('quiz-options').innerHTML = '';
    document.getElementById('quiz-score').textContent = `Final Score: ${quizScore}/${quizData.length}`;
    document.getElementById('quiz-feedback').innerHTML = '';
    return;
  }

  const q = quizData[currentQuestion];
  document.getElementById('quiz-question').innerHTML = `<h3>Question ${currentQuestion + 1}</h3><p>${q.question}</p>`;
  
  const optionsHtml = q.options.map((opt, idx) => 
    `<button class="quiz-option btn" data-idx="${idx}">${opt}</button>`
  ).join('');
  document.getElementById('quiz-options').innerHTML = optionsHtml;
  document.getElementById('quiz-feedback').innerHTML = '';
  document.getElementById('quiz-score').textContent = `Score: ${quizScore}/${quizData.length}`;

  document.querySelectorAll('.quiz-option').forEach(btn => {
    btn.addEventListener('click', (e) => checkAnswer(e.target.dataset.idx));
  });
}

function checkAnswer(idx) {
  const q = quizData[currentQuestion];
  const correct = parseInt(idx) === q.correct;
  
  if (correct) quizScore++;
  
  document.getElementById('quiz-feedback').innerHTML = `
    <div class="card" style="background: ${correct ? '#d4edda' : '#f8d7da'}; padding: 1rem;">
      <strong>${correct ? 'Correct!' : 'Incorrect'}</strong>
      <p>${q.explanation}</p>
      <button class="btn btn--primary" onclick="nextQuestion()">Next Question</button>
    </div>
  `;
}

function nextQuestion() {
  currentQuestion++;
  showQuestion();
}

// ===== Password Age Calculator =====
document.getElementById('check-age-btn').addEventListener('click', async () => {
  const password = document.getElementById('age-pwd').value;
  const createdDate = document.getElementById('pwd-created-date').value;
  const accountType = document.getElementById('account-type').value;

  if (!password || !createdDate) {
    alert('Please enter password and creation date');
    return;
  }

  try {
    const res = await fetch('/age-calculator', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, created_date: createdDate, account_type: accountType })
    });
    const data = await res.json();

    const resultDiv = document.getElementById('age-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <h3>Password Age Analysis</h3>
      <p><strong>Current Age:</strong> ${data.age_days} days</p>
      <p><strong>Status:</strong> <span style="color: ${data.status === 'expired' ? '#ff5f6d' : '#39d98a'}">${data.status.toUpperCase()}</span></p>
      <p><strong>Days Until Change:</strong> ${data.days_until_change}</p>
      <p><strong>Next Change Date:</strong> ${new Date(data.next_change_date).toLocaleDateString()}</p>
      <p><strong>Recommended Interval:</strong> ${data.recommended_interval} days</p>
      <p><strong>Current Strength:</strong> ${data.strength_score}%</p>
    `;
  } catch (err) {
    alert('Failed to calculate password age');
  }
});

// ===== Batch Analysis =====
document.getElementById('batch-analyze-btn').addEventListener('click', async () => {
  const textarea = document.getElementById('batch-passwords');
  const passwords = textarea.value.split('\n').filter(p => p.trim());

  if (passwords.length === 0) {
    alert('Please enter passwords to analyze');
    return;
  }

  try {
    const res = await fetch('/batch-analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ passwords })
    });
    const data = await res.json();

    const stats = data.statistics;
    let html = `
      <div class="card">
        <h3>Batch Analysis Results</h3>
        <p><strong>Total Analyzed:</strong> ${stats.total}</p>
        <p><strong>Average Score:</strong> ${stats.average_score}%</p>
        <p><strong>Weak:</strong> ${stats.weak} | <strong>Medium:</strong> ${stats.medium} | <strong>Strong:</strong> ${stats.strong}</p>
        <p><strong>Leaked:</strong> ${stats.leaked}</p>
        <h4 style="margin-top:1rem;">Individual Results:</h4>
        <div style="max-height:300px; overflow-y:auto;">
    `;

    data.results.forEach(r => {
      html += `
        <div style="padding:0.5rem; border-bottom:1px solid #333;">
          <span class="badge badge--${r.label === 'Strong' ? 'success' : r.label === 'Medium' ? 'warning' : 'danger'}">${r.label}</span>
          Score: ${r.score}% | Length: ${r.length} | Entropy: ${r.entropy} bits
          ${r.leaked ? ' <span style="color:#ff5f6d;">⚠️ LEAKED</span>' : ''}
        </div>
      `;
    });

    html += '</div></div>';
    document.getElementById('batch-results').innerHTML = html;
  } catch (err) {
    alert('Batch analysis failed');
  }
});

// ===== Export & Report =====
document.getElementById('export-json-btn').addEventListener('click', async () => {
  const password = document.getElementById('export-pwd').value;
  if (!password) {
    alert('Please enter a password');
    return;
  }

  try {
    const res = await fetch('/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, format: 'json' })
    });
    const data = await res.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `password-analysis-${Date.now()}.json`;
    a.click();
  } catch (err) {
    alert('Export failed');
  }
});

document.getElementById('generate-report-btn').addEventListener('click', async () => {
  const password = document.getElementById('export-pwd').value;
  if (!password) {
    alert('Please enter a password');
    return;
  }

  try {
    const res = await fetch('/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    const data = await res.json();

    const reportDiv = document.getElementById('report-output');
    reportDiv.style.display = 'block';
    reportDiv.innerHTML = `
      <h3>Security Report</h3>
      <p><em>Generated: ${new Date(data.timestamp).toLocaleString()}</em></p>
      
      <h4>Executive Summary</h4>
      <p><strong>Score:</strong> ${data.executive_summary.score}% (${data.executive_summary.label})</p>
      <p><strong>Verdict:</strong> <span style="color: ${data.executive_summary.verdict === 'Pass' ? '#39d98a' : '#ff5f6d'}">${data.executive_summary.verdict}</span></p>
      
      <h4>Detailed Analysis</h4>
      <p><strong>Length:</strong> ${data.detailed_analysis.length} characters</p>
      <p><strong>Entropy:</strong> ${data.detailed_analysis.entropy} bits</p>
      <p><strong>Unique Characters:</strong> ${data.detailed_analysis.unique_characters}</p>
      <p><strong>Character Types:</strong> Lower: ${data.detailed_analysis.character_types.lowercase}, Upper: ${data.detailed_analysis.character_types.uppercase}, Digits: ${data.detailed_analysis.character_types.digits}, Special: ${data.detailed_analysis.character_types.special}</p>
      
      <h4>Security Issues</h4>
      <ul>${data.security_issues.map(i => '<li>' + i + '</li>').join('')}</ul>
      
      <h4>Breach Status</h4>
      <p>${data.breach_status.message}</p>
      
      <h4>Crack Resistance</h4>
      <p>${data.crack_resistance}</p>
      
      <h4>Compliance</h4>
      <p>NIST Guidelines: ${data.compliance.nist_guidelines ? '✓' : '✗'}</p>
      <p>PCI DSS: ${data.compliance.pci_dss ? '✓' : '✗'}</p>
      <p>HIPAA: ${data.compliance.hipaa ? '✓' : '✗'}</p>
      
      <h4>Recommendations</h4>
      <ul>${data.recommendations.map(r => '<li>' + r + '</li>').join('')}</ul>
    `;
  } catch (err) {
    alert('Report generation failed');
  }
});

// ===== Custom Wordlist Upload =====
document.getElementById('upload-wordlist-btn').addEventListener('click', async () => {
  const textarea = document.getElementById('wordlist-input');
  const words = textarea.value.split('\n').filter(w => w.trim());

  if (words.length === 0) {
    alert('Please enter words');
    return;
  }

  try {
    const res = await fetch('/wordlist/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, name: 'custom' })
    });
    const data = await res.json();

    document.getElementById('wordlist-status').innerHTML = `
      <div class="card" style="background:#d4edda; padding:1rem;">
        <strong>Success!</strong> Uploaded ${data.word_count} words to "${data.name}" wordlist.
      </div>
    `;
  } catch (err) {
    alert('Wordlist upload failed');
  }
});

// ===== Attack Visualization =====
document.querySelectorAll('.attack-btn').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    const attackType = e.target.dataset.attack;
    
    try {
      const res = await fetch('/attack-viz/data');
      const data = await res.json();
      const attack = data[attackType];

      const detailsDiv = document.getElementById('attack-details');
      detailsDiv.style.display = 'block';
      detailsDiv.innerHTML = `
        <h3>${attackType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
        <p>${attack.description}</p>
        
        <h4>How It Works:</h4>
        <ol>${attack.steps.map(s => '<li>' + s + '</li>').join('')}</ol>
        
        <p><strong>Complexity:</strong> ${attack.complexity}</p>
        <p><strong>Typical Speed:</strong> ${attack.typical_speed}</p>
      `;
    } catch (err) {
      alert('Failed to load attack data');
    }
  });
});

// ===== Breach Checker =====
breachCheckBtn.addEventListener('click', async () => {
  const password = breachPassword.value;
  
  if (!password) {
    alert('Please enter a password to check');
    return;
  }

  breachCheckBtn.disabled = true;
  breachCheckBtn.textContent = 'Checking...';
  
  // Add running animation to breach panel
  const breachPanel = document.getElementById('breach-checker');
  if (breachPanel) {
    breachPanel.classList.add('running');
  }

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });

    const data = await res.json();
    const leakCheck = data.leaked_check;

    // Show results
    breachResults.style.display = 'block';
    
    // Update status and styling based on breach status
    if (leakCheck.is_leaked) {
      breachResultStatus.textContent = '⚠️ BREACHED';
      breachResultStatus.style.color = '#ff5f6d';
      breachIcon.textContent = '🔓';
      breachResultCard.style.borderColor = 'rgba(255, 95, 109, 0.5)';
      breachResultCard.style.background = 'rgba(255, 95, 109, 0.1)';
      
      // Severity badge
      const severityColors = {
        'critical': '#ff3860',
        'high': '#ff7a59',
        'medium': '#ffb84d'
      };
      
      let badgeHTML = `
        <span class="badge" style="background: ${severityColors[leakCheck.severity]}; color: #0a0c12;">
          ${leakCheck.severity.toUpperCase()} RISK
        </span>
      `;
      
      // Add breach count if available
      if (leakCheck.breach_count !== undefined) {
        badgeHTML += `
          <span class="badge" style="background: rgba(255, 95, 109, 0.2); color: #ffb3ba; margin-left: 8px;">
            Seen ${leakCheck.breach_count.toLocaleString()} times
          </span>
        `;
      }
      
      // Add source badge
      if (leakCheck.source) {
        badgeHTML += `
          <span class="badge badge--muted" style="margin-left: 8px; font-size: 11px;">
            ${leakCheck.source}
          </span>
        `;
      }
      
      breachSeverityBadge.innerHTML = badgeHTML;
    } else {
      breachResultStatus.textContent = '✓ SAFE';
      breachResultStatus.style.color = '#39d98a';
      breachIcon.textContent = '🔒';
      breachResultCard.style.borderColor = 'rgba(57, 217, 138, 0.5)';
      breachResultCard.style.background = 'rgba(57, 217, 138, 0.1)';
      
      let badgeHTML = `
        <span class="badge badge--success">
          NO BREACH DETECTED
        </span>
      `;
      
      // Add source badge
      if (leakCheck.source) {
        badgeHTML += `
          <span class="badge badge--muted" style="margin-left: 8px; font-size: 11px;">
            Verified via ${leakCheck.source}
          </span>
        `;
      }
      
      breachSeverityBadge.innerHTML = badgeHTML;
    }

    breachResultMessage.textContent = leakCheck.message;

  } catch (err) {
    alert('Failed to check breach status');
  } finally {
    breachCheckBtn.disabled = false;
    breachCheckBtn.textContent = 'Check Breach';
    
    // Remove running animation
    if (breachPanel) {
      breachPanel.classList.remove('running');
    }
  }
});

// Clear breach checker results
breachClearBtn.addEventListener('click', () => {
  breachPassword.value = '';
  breachResults.style.display = 'none';
  breachResultStatus.textContent = '-';
  breachResultMessage.textContent = '';
  breachSeverityBadge.innerHTML = '';
  breachIcon.textContent = '';
  breachResultCard.style.borderColor = '';
  breachResultCard.style.background = '';
});

// Allow Enter key to trigger breach check
breachPassword.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    breachCheckBtn.click();
  }
});
