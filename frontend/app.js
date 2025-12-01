// Frontend logic: loads questions.json, starts session locally and submits answers to /api/submit
const apiBase = "https://azurequizprod-api.azurewebsites.net/api/SubmitFunction";
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
  
  // --- START: Validation Logic (Start Test) ---
  const schoolRegex = /^[A-Z]{3}\d{3}$/; 
  const studentRegex = /^\d{3}$/; 

  if(!school || !student){
    alert('Enter school code and roll number.');
    return;
  }

  if (!schoolRegex.test(school)) {
    alert('Invalid School Code. It must be 3 uppercase city letters followed by 3 digits (e.g., BLR123).');
    return;
  }

  if (!studentRegex.test(student)) {
    alert('Invalid Roll Number. It must be exactly 3 digits (e.g., 001 or 999).');
    return;
  }
  
  const rollNumber = parseInt(student, 10);
  if (rollNumber === 0) {
    alert('Invalid Roll Number. The roll number cannot be 000.');
    return;
  }
  // --- END: Validation Logic (Start Test) ---

  sessionToken = `${school}#${student}#${Date.now()}`;
  await loadQuestions();
  renderQuestions();
  document.getElementById('intro').style.display = 'none';
  document.getElementById('quiz').style.display = 'block';
});

document.getElementById('submit').addEventListener('click', async () => {
  if(!sessionToken){ alert('Start test first'); return; }
  
  const answers = [];
  let attemptedCount = 0; 
  
  for(let i=0;i<questions.length;i++){
    const radios = document.getElementsByName('q'+i);
    let sel = null;
    
    radios.forEach(r => { 
      if(r.checked) sel = Number(r.value); // Convert string value to number
    });
    
    // Check if an answer was selected
    if (sel !== null) {
      attemptedCount++; 
    }
    
    answers.push(sel);
  }
  
  // Check: Ensure at least one question was attempted
  if (attemptedCount === 0) {
    alert('You must attempt at least one question before submitting the test.');
    return; 
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
  
  console.log('Submission Payload:', payload); // Debugging line for server issue

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
  
  // Display Score: Correct Answers / Attempted Questions
  rdiv.innerHTML = `<h3>Submitted</h3><p>Score: ${out.score} / ${attemptedCount}</p>`;
});
