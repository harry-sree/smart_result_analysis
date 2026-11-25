import pandas as pd
import numpy as np

def clean(df):
    df=df.copy()
    for c in ['internal_marks','assignment_marks','attendance','previous_score','final_score']:
        if c in df: df[c]=pd.to_numeric(df[c],errors='coerce')
    if 'result' in df: df['result']=df['result'].astype(str).str.strip().str.title()
    return df

def dashboard_data(df):
    df=clean(df); total=len(df)
    students=df.student_id.nunique() if 'student_id' in df else total
    subjects=df.subject.nunique() if 'subject' in df else 0
    passed=int((df.result=='Pass').sum()) if 'result' in df else 0
    failed=int((df.result=='Fail').sum()) if 'result' in df else 0
    return {'kpis':{'total_students':int(students),'total_subjects':int(subjects),'avg_score':round(df.final_score.mean(),2),'avg_attendance':round(df.attendance.mean(),2),'pass_percentage':round(passed/(passed+failed)*100,2) if passed+failed else 0,'at_risk':0},'subject':df.groupby('subject',as_index=False).final_score.mean().round(2).rename(columns={'final_score':'average'}).to_dict('records'),'class_data':df.groupby('class',as_index=False).final_score.mean().round(2).rename(columns={'final_score':'average'}).to_dict('records'),'result':df.result.value_counts().rename_axis('result').reset_index(name='count').to_dict('records'),'score_distribution':score_distribution(df),'attendance_score':df[['attendance','final_score']].dropna().to_dict('records')}

def score_distribution(df):
    bins=[-np.inf,39,49,59,69,79,89,np.inf]; labels=['0-39','40-49','50-59','60-69','70-79','80-89','90-100']
    x=pd.cut(df.final_score,bins=bins,labels=labels).value_counts(sort=False).reset_index(); x.columns=['range','count']; return x.to_dict('records')

def analysis_data(df):
    df=clean(df); out={}
    out['internal_final']=df[['internal_marks','final_score']].dropna().to_dict('records')
    out['previous_final']=df[['previous_score','final_score']].dropna().to_dict('records')
    out['gender']=df.groupby('gender',as_index=False).final_score.mean().round(2).rename(columns={'final_score':'average'}).to_dict('records') if 'gender' in df else []
    out['subject']=df.groupby('subject',as_index=False).final_score.mean().round(2).rename(columns={'final_score':'average'}).to_dict('records')
    return out

def student_data(df, student_id):
    df=clean(df); s=df[df.student_id.astype(str)==str(student_id)]
    if s.empty:return None
    return {'student_id':str(student_id),'student_name':s.student_name.iloc[0],'subjects':s[['subject','final_score','attendance']].to_dict('records'),'previous_final':s[['subject','previous_score','final_score']].to_dict('records')}

def subject_data(df):
    df=clean(df); out={}
    for name,s in df.groupby('subject'):
        out[str(name)]={'average':round(s.final_score.mean(),2),'attendance':round(s.attendance.mean(),2),'results':s.result.value_counts().rename_axis('result').reset_index(name='count').to_dict('records')}
    return out

def class_data(df):
    df=clean(df); out={}
    for name,s in df.groupby('class'):
        out[str(name)]={'average':round(s.final_score.mean(),2),'attendance':round(s.attendance.mean(),2),'subjects':s.groupby('subject',as_index=False).final_score.mean().round(2).rename(columns={'final_score':'average'}).to_dict('records')}
    return out
