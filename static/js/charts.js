const PLOTLY='https://cdn.plot.ly/plotly-2.35.2.min.js';
function loadPlotly(cb){if(window.Plotly)return cb();let s=document.createElement('script');s.src=PLOTLY;s.onload=cb;document.head.appendChild(s)}
function layout(title,x='',y=''){return{title:{text:title,font:{size:18}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{l:55,r:25,t:55,b:55},xaxis:{title:x,gridcolor:'#e5e7eb'},yaxis:{title:y,gridcolor:'#e5e7eb'},font:{family:'Inter,Arial,sans-serif'},responsive:true}}
function draw(id,traces,l,config){let e=document.getElementById(id);if(e)Plotly.newPlot(e,traces,l,config||{responsive:true,displaylogo:false})}
function renderDashboardCharts(d){loadPlotly(()=>{draw('resultChart',[{labels:d.result.map(x=>x.result),values:d.result.map(x=>x.count),type:'pie',hole:.55,textinfo:'label+percent'}],layout('Overall Pass / Fail'));draw('subjectChart',[{x:d.subject.map(x=>x.subject),y:d.subject.map(x=>x.average),type:'bar',text:d.subject.map(x=>x.average),textposition:'auto'}],layout('Average Score by Subject','Subject','Average Score'));draw('classChart',[{x:d.class_data.map(x=>x.class),y:d.class_data.map(x=>x.average),type:'bar',text:d.class_data.map(x=>x.average),textposition:'auto'}],layout('Class-wise Average Score','Class','Average Score'));draw('scoreDistribution',[{x:d.score_distribution.map(x=>x.range),y:d.score_distribution.map(x=>x.count),type:'bar'}],layout('Final Score Distribution','Score Range','Students'));draw('attendanceScore',[{x:d.attendance_score.map(x=>x.attendance),y:d.attendance_score.map(x=>x.final_score),mode:'markers',type:'scatter',marker:{size:9,opacity:.7}}],layout('Attendance vs Final Score','Attendance (%)','Final Score'))})}
function renderAnalysisCharts(d){loadPlotly(()=>{draw('internalFinalChart',[{x:d.internal_final.map(x=>x.internal_marks),y:d.internal_final.map(x=>x.final_score),mode:'markers',type:'scatter'}],layout('Internal Marks vs Final Score','Internal Marks','Final Score'));draw('previousFinalChart',[{x:d.previous_final.map(x=>x.previous_score),y:d.previous_final.map(x=>x.final_score),mode:'markers',type:'scatter'}],layout('Previous Score vs Final Score','Previous Score','Final Score'));draw('genderChart',[{x:d.gender.map(x=>x.gender),y:d.gender.map(x=>x.average),type:'bar'}],layout('Gender-wise Average Score','Gender','Average Score'));draw('analysisSubjectChart',[{x:d.subject.map(x=>x.subject),y:d.subject.map(x=>x.average),type:'bar'}],layout('Subject Performance','Subject','Average Score'))})}
function renderClassificationCharts(r){loadPlotly(()=>{let n=Object.keys(r);draw('classificationMetrics',['accuracy','precision','recall','f1'].map(k=>({x:n,y:n.map(x=>r[x][k]),name:k.toUpperCase(),type:'bar'})),{...layout('Classification Model Comparison','Model','Score'),barmode:'group',yaxis:{range:[0,1],title:'Metric Score'}})})}
function renderRegressionCharts(r){loadPlotly(()=>{let n=Object.keys(r);draw('regressionMetrics',['mae','rmse','r2'].map(k=>({x:n,y:n.map(x=>r[x][k]),name:k.toUpperCase(),type:'bar'})),{...layout('Regression Model Comparison','Model','Metric'),barmode:'group'})})}
function renderStudentCharts(d){loadPlotly(()=>{draw('studentMarks',[{x:d.subjects.map(x=>x.subject),y:d.subjects.map(x=>x.final_score),type:'bar'}],layout('Final Score by Subject','Subject','Final Score'));draw('studentAttendance',[{x:d.subjects.map(x=>x.subject),y:d.subjects.map(x=>x.attendance),type:'bar'}],layout('Attendance by Subject','Subject','Attendance (%)'));draw('studentPreviousFinal',[{x:d.previous_final.map(x=>x.subject),y:d.previous_final.map(x=>x.previous_score),name:'Previous Score',type:'bar'},{x:d.previous_final.map(x=>x.subject),y:d.previous_final.map(x=>x.final_score),name:'Final Score',type:'bar'}],{...layout('Previous vs Final Score','Subject','Score'),barmode:'group'})})}
function renderSubjectCharts(d){loadPlotly(()=>{let n=Object.keys(d);draw('subjectAverage',[{x:n,y:n.map(x=>d[x].average),type:'bar'}],layout('Average Score by Subject','Subject','Average Score'));draw('subjectAttendance',[{x:n,y:n.map(x=>d[x].attendance),type:'bar'}],layout('Average Attendance by Subject','Subject','Attendance (%)'));draw('subjectResult',[{x:n,y:n.map(x=>(d[x].results.find(r=>r.result==='Pass')||{count:0}).count),name:'Pass',type:'bar'},{x:n,y:n.map(x=>(d[x].results.find(r=>r.result==='Fail')||{count:0}).count),name:'Fail',type:'bar'}],{...layout('Pass / Fail by Subject','Subject','Students'),barmode:'group'})})}
function renderClassCharts(d){loadPlotly(()=>{let n=Object.keys(d);draw('classAverage',[{x:n,y:n.map(x=>d[x].average),type:'bar'}],layout('Average Score by Class','Class','Average Score'));draw('classAttendance',[{x:n,y:n.map(x=>d[x].attendance),type:'bar'}],layout('Average Attendance by Class','Class','Attendance (%)'));let a=[];n.forEach(c=>(d[c].subjects||[]).forEach(s=>a.push({label:c+' - '+s.subject,average:s.average})));draw('classSubject',[{x:a.map(x=>x.label),y:a.map(x=>x.average),type:'bar'}],layout('Class and Subject Performance','Class - Subject','Average Score'))})}
function renderRiskCharts(r){loadPlotly(()=>{r=[...r].sort((a,b)=>b.failure_probability-a.failure_probability);draw('riskChart',[{x:r.map(x=>x.student_name||x.student_id),y:r.map(x=>x.failure_probability*100),type:'bar',text:r.map(x=>(x.failure_probability*100).toFixed(1)+'%'),textposition:'auto'}],layout('Failure Probability by Student','Student','Failure Probability (%)'))})}



// Render visualizations only on the page/module that owns the chart placeholders.
document.addEventListener('DOMContentLoaded', function () {
  const node = document.getElementById('pageChartData');
  if (!node) return;
  let d; try { d = JSON.parse(node.textContent); } catch (e) { console.error('Invalid page chart data', e); return; }
  loadPlotly(function () {
    const cfg = {responsive:true, displaylogo:false};
    const pieLayout = (title) => ({...layout(title), showlegend:true});
    const bar = (id, labels, values, title, x, y) => draw(id,[{x:labels,y:values,type:'bar',text:values.map(v=>Number(v).toFixed(2)),textposition:'auto'}],layout(title,x,y),cfg);
    const grouped = (id, labels, a, b, title, x, y, an='Pass', bn='Fail') => draw(id,[{x:labels,y:a,name:an,type:'bar'},{x:labels,y:b,name:bn,type:'bar'}],{...layout(title,x,y),barmode:'group'},cfg);
    if (document.getElementById('dashResultChart')) {
      draw('dashResultChart',[{labels:d.result_labels,values:d.result_values,type:'pie',hole:.45,textinfo:'label+percent'}],pieLayout('Overall Pass / Fail Distribution'),cfg);
      bar('dashSubjectChart',d.subject_labels,d.subject_values,'Average Final Score by Subject','Subject','Average Score');
      bar('dashClassChart',d.class_labels,d.class_values,'Average Final Score by Class','Class','Average Score');
      draw('dashGenderChart',[{labels:d.gender_labels,values:d.gender_values,type:'pie',hole:.45,textinfo:'label+percent'}],pieLayout('Student Gender Distribution'),cfg);
    }
    if (document.getElementById('analysisSubjectChart')) {
      const labels=Object.keys(d.subjects||{}), vals=Object.values(d.subjects||{});
      bar('analysisSubjectChart',labels,vals,'Subject-wise Average Marks','Subject','Average Marks');
      const summary=d.summary||{};
      draw('analysisAttendanceChart',[{x:['Average Attendance'],y:[Number(summary.attendance||0)],type:'bar',text:[String(summary.attendance||0)],textposition:'auto'}],layout('Average Attendance','Dataset','Attendance (%)'),cfg);
    }
    if (document.getElementById('subjectAverageChart')) {
      const labels=d.map(x=>x.subject), avg=d.map(x=>Number(x.average_marks)), pass=d.map(x=>Number(x.pass_count)), fail=d.map(x=>Number(x.fail_count));
      bar('subjectAverageChart',labels,avg,'Average Marks by Subject','Subject','Average Marks');
      grouped('subjectPassFailChart',labels,pass,fail,'Pass / Fail Count by Subject','Subject','Students');
      bar('subjectAttendanceChart',labels,d.map(x=>Number(x.average_attendance)),'Average Attendance by Subject','Subject','Attendance (%)');
    }
    if (document.getElementById('classAverageChart')) {
      const labels=d.map(x=>String(x.class)), avg=d.map(x=>Number(x.average_score));
      bar('classAverageChart',labels,avg,'Average Score by Class','Class','Average Score');
      grouped('classPassFailChart',labels,d.map(x=>Number(x.pass_count)),d.map(x=>Number(x.fail_count)),'Pass / Fail Count by Class','Class','Students');
      grouped('classPassFailPercentageChart',labels,d.map(x=>Number(x.pass_percentage)),d.map(x=>Number(x.fail_percentage)),'Pass / Fail Percentage by Class','Class','Percentage (%)','Pass %','Fail %');
      grouped('classGenderPercentageChart',labels,d.map(x=>Number(x.male_percentage)),d.map(x=>Number(x.female_percentage)),'Male / Female Percentage by Class','Class','Percentage (%)','Male %','Female %');
    }
    if (document.getElementById('studentsScoreChart')) {
      const labels=d.map(x=>String(x.student_name)), scores=d.map(x=>Number(x.average_score));
      bar('studentsScoreChart',labels,scores,'Student Average Scores','Student','Average Score');
      const genders={}; d.forEach(x=>genders[x.gender]=(genders[x.gender]||0)+1);
      draw('studentsGenderChart',[{labels:Object.keys(genders),values:Object.values(genders),type:'pie',hole:.4,textinfo:'label+percent'}],pieLayout('Students by Gender'),cfg);
      bar('studentsAttendanceChart',labels,d.map(x=>Number(x.attendance)),'Student Attendance','Student','Attendance (%)');
    }
    if (document.getElementById('detailMarksChart')) {
      const labels=d.map(x=>String(x.subject));
      draw('detailMarksChart',[
        {x:labels,y:d.map(x=>Number(x.internal_marks)),name:'Internal Marks',type:'bar'},
        {x:labels,y:d.map(x=>Number(x.assignment_marks)),name:'Assignment Marks',type:'bar'},
        {x:labels,y:d.map(x=>Number(x.previous_score)),name:'Previous Score',type:'bar'},
        {x:labels,y:d.map(x=>Number(x.final_score)),name:'Final Score',type:'bar'}
      ],{...layout('Subject-wise Student Marks Comparison','Subject','Marks / Score'),barmode:'group'},cfg);
      bar('detailAttendanceChart',labels,d.map(x=>Number(x.attendance)),'Attendance by Subject','Subject','Attendance (%)');
      const resultCounts={};
      d.forEach(x=>{const result=String(x.result||'Unknown');resultCounts[result]=(resultCounts[result]||0)+1;});
      draw('detailResultPieChart',[{labels:Object.keys(resultCounts),values:Object.values(resultCounts),type:'pie',hole:.4,textinfo:'label+value+percent'}],pieLayout('Student Pass / Fail Result Distribution'),cfg);
      draw('detailScoreComparisonChart',[
        {x:labels,y:d.map(x=>Number(x.previous_score)),name:'Previous Score',type:'bar'},
        {x:labels,y:d.map(x=>Number(x.final_score)),name:'Final Score',type:'bar'}
      ],{...layout('Previous vs Final Score','Subject','Score'),barmode:'group'},cfg);
    }
    if (document.getElementById('classificationMetricsChart')) {
      const labels=d.map(x=>x.model);
      grouped('classificationMetricsChart',labels,d.map(x=>Number(x.accuracy)),d.map(x=>Number(x.f1_score)),'Classification Model Metrics','Model','Percent','Accuracy (%)','F1 Score (%)');
    }
    if (document.getElementById('regressionMetricsChart')) {
      const labels=Object.keys(d), rows=Object.values(d);
      grouped('regressionMetricsChart',labels,rows.map(x=>Number(x.mae)),rows.map(x=>Number(x.rmse)),'Regression Error Comparison','Model','Error','MAE','RMSE');
    }
    if (document.getElementById('riskProbabilityChart')) {
      const rows=[...d].sort((a,b)=>Number(b.failure_probability)-Number(a.failure_probability));
      bar('riskProbabilityChart',rows.map(x=>String(x.student_name||x.student_id)),rows.map(x=>Number(x.failure_probability)),'Predicted Failure Probability by Student','Student','Failure Probability (%)');
    }
  });
});
