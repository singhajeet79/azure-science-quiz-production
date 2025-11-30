// Frontend logic: loads questions.json, starts session locally and submits answers to /api/submit
const apiBase = "/api/SubmitFunction";

let questions = [];
let sessionToken = null;

async function loadQuestions(){
  const r = await fetch('questions.json');
  const data = await r.json();
  questions = data.questions;
  return data;
}

function renderQuestions(){
  const qdiv = document.getElementById('questions');
  qdiv.innerHTML = '';
  questions.forEach((q, i) => {
    const out = document.createElement('div');
    out.className = 'card';
    out.innerHTML = `<p><strong>${i+1}. ${q.text}</strong></p>` +
      q.choices.map((c, idx) => `<label><input type="radio" name="q${i}" value="${idx}"> ${c}</label><br>`).join('');
    qdiv.appendChild(out);
  });
}

document.getElementById('start').addEventListener('click', async () => {
  const school = document.getElementById('school').value.trim();
  const student = document.getElementById('student').value.trim();
  
  // --- Validation Logic ---
  // 1. School Code: 3 uppercase letters + 3 digits (e.g., BLR123)
  const schoolRegex = /^[A-Z]{3}\d{3}$/; 
  // 2. Roll Number: Exactly 3 digits (000-999 format check)
  const studentRegex = /^\d{3}$/; 

  if(!school || !student){
    alert('Enter school code and roll number.');
    return;
  }

  if (!schoolRegex.test(school)) {
    alert('Invalid School Code!');
    return;
  }

  // First, check if it's 3 digits
  if (!studentRegex.test(student)) {
    alert('Invalid Roll Number!');
    return;
  }
  
  // Second, check the value to ensure it's not 000
  // parseInt treats '000', '001', '999' as 0, 1, and 999 respectively.
  const rollNumber = parseInt(student, 10);
  if (rollNumber === 0) {
    alert('Invalid Roll Number. The roll number cannot be 000.');
    return;
  }
  // ---------------------------

  // Validation passed, proceed with starting the test
  // Local "session token" (simple); production: use issuer token from API
  sessionToken = `${school}#${student}#${Date.now()}`;
  await loadQuestions();
  renderQuestions();
  document.getElementById('intro').style.display = 'none';
  document.getElementById('quiz').style.display = 'block';
});

document.getElementById('submit').addEventListener('click', async () => {
  if(!sessionToken){ alert('Start test first'); return; }
  const answers = [];
  for(let i=0;i<questions.length;i++){
    const radios = document.getElementsByName('q'+i);
    let sel = null;
    radios.forEach(r => { if(r.checked) sel = Number(r.value); });
    answers.push(sel);
  }

  // Add lightweight client-side jitter to reduce burst risk
  await new Promise(res => setTimeout(res, Math.floor(Math.random()*8000)));

  const payload = {
    sessionToken,
    school: document.getElementById('school').value,
    student: document.getElementById('student').value,
    grade: document.getElementById('grade').value,
    answers
  };

  const res = await fetch(apiBase, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if(!res.ok){
    const txt = await res.text();
    alert('Submit failed: ' + txt);
    return;
  }
  const out = await res.json();
  document.getElementById('quiz').style.display = 'none';
  const rdiv = document.getElementById('result');
  rdiv.style.display = 'block';
  rdiv.innerHTML = `<h3>Submitted</h3><p>Score (server-calculated): ${out.score} / ${questions.length}</p><p>AttemptId: ${out.attemptId}</p>`;
});
