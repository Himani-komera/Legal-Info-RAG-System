from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import pymysql
from transformers import AutoTokenizer, RagRetriever, RagSequenceForGeneration, RagTokenForGeneration
import torch
import faiss
import numpy as np
import pandas as pd
import pickle
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config
import torch
from transformers import pipeline
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import subprocess
import speech_recognition as sr

global username

tokenizer = AutoTokenizer.from_pretrained("facebook/rag-sequence-nq")
retriever = RagRetriever.from_pretrained("facebook/rag-sequence-nq", index_name="exact", use_dummy_dataset=True)
model = RagSequenceForGeneration.from_pretrained("facebook/rag-token-nq", retriever=retriever)

seq = T5ForConditionalGeneration.from_pretrained('t5-small')
seq2seq_model = T5Tokenizer.from_pretrained('t5-small',model_max_length=512)
device = torch.device('cpu')

dataset = pd.read_csv("LegalDocument/legal_text.csv", usecols=['case_text'])
dataset = dataset.values
recognizer = sr.Recognizer()

if os.path.exists("model/faiss.pckl"):
    f = open('model/faiss.pckl', 'rb')
    faiss_index = pickle.load(f)
    f.close() 
else:
    rag = []
    for i in range(0, 100):
        try:
            data = dataset[i,0].strip('\n').strip().lower()
            data = data[0:2500]
            inputs = tokenizer(data, return_tensors="pt")
            input_ids = inputs["input_ids"]
            question_hidden_states = model.question_encoder(input_ids)[0]
            question_hidden_states = question_hidden_states.detach().numpy().ravel()
            rag.append(question_hidden_states)
            print(str(i)+" "+str(len(data)))
        except:
            pass
    rag = np.asarray(rag)
    print(rag.shape)
    dimension = rag.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(rag)
    print(faiss_index)
    f = open('model/faiss.pckl', 'wb')
    pickle.dump(index, f)
    f.close()

@csrf_exempt
def record(request):
    if request.method == "POST":
        global tokenizer, faiss_index, dataset
        audio_data = request.FILES.get('data')
        fs = FileSystemStorage()
        if os.path.exists('LegalApp/static/record.wav'):
            os.remove('LegalApp/static/record.wav')
        if os.path.exists('LegalApp/static/record1.wav'):
            os.remove('LegalApp/static/record1.wav')    
        fs.save('LegalApp/static/record.wav', audio_data)
        path = 'E:/venkat/feb25/LegalDocument/LegalApp/static/'
        res = subprocess.check_output(path+'ffmpeg.exe -i '+path+'record.wav '+path+'record1.wav', shell=True)
        with sr.WavFile('LegalApp/static/record1.wav') as source:
            audio = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio)
            print(question)
        except Exception as ex:
            question = "unable to recognize"
        reply =  "unable to recognize"
        if question != "unable to recognize":
            inputs = tokenizer(question, return_tensors="pt")
            input_ids = inputs["input_ids"]
            query = model.question_encoder(input_ids)[0]
            query = query.detach().numpy()
            print(query.shape)
            distances, indices = faiss_index.search(query, k=1)
            reply = ""
            for i, idx in enumerate(indices[0]):
                reply += str(dataset[idx,0])
                break
        return HttpResponse("Chatbot: "+reply, content_type="text/plain")     

def VoiceChatbot(request):
    if request.method == 'GET':
        return render(request, 'VoiceChatbot.html', {})      

def SummarizeAction(request):
    if request.method == 'POST':
        global seq2seq_model
        myfile = request.FILES['t1'].read()
        myfile = myfile.decode()
        tokenizedText = seq2seq_model.encode(myfile, return_tensors='pt', max_length=512, truncation=True).to(device)
        summaryIds = seq.generate(tokenizedText, min_length=30, max_length=120)
        predict = seq2seq_model.decode(summaryIds[0], skip_special_tokens=True)
        output = "<font size=3 color=blue>Input Text = </font>"+myfile+"<br/><br/>"
        output += "<font size=3 color=blue>Generated Summary = </font>"+predict
        context= {'data': output}
        return render(request, 'UserScreen.html', context)

def Summarize(request):
    if request.method == 'GET':
        return render(request, 'Summarize.html', {})         

@csrf_exempt
def ChatData(request):
    if request.method == 'GET':
        global tokenizer, faiss_index, dataset
        question = request.GET.get('mytext', False)
        inputs = tokenizer(question, return_tensors="pt")
        input_ids = inputs["input_ids"]
        query = model.question_encoder(input_ids)[0]
        query = query.detach().numpy()
        print(query.shape)
        distances, indices = faiss_index.search(query, k=1)
        output = ""
        for i, idx in enumerate(indices[0]):
            output += str(dataset[idx,0])
            break
        return HttpResponse("Chatbot: "+output, content_type="text/plain")       

def Chatbot(request):
    if request.method == 'GET':
        return render(request, 'Chatbot.html', {})       

def LegalAdviceAction(request):
    if request.method == 'POST':
        global tokenizer, faiss_index, dataset
        data = request.POST.get('t1', False)
        inputs = tokenizer(data, return_tensors="pt")
        input_ids = inputs["input_ids"]
        query = model.question_encoder(input_ids)[0]
        query = query.detach().numpy()
        print(query.shape)
        distances, indices = faiss_index.search(query, k=3)
        output = ""
        for i, idx in enumerate(indices[0]):
            output += '<center><font size="3" color="blue">Recommendation '+str(i)+"</font></center><br/>"
            output += str(dataset[idx,0])+"<br/><br/>"
        context= {'data': output}
        return render(request, 'UserScreen.html', context)    

def LegalAdvice(request):
    if request.method == 'GET':
        return render(request, 'LegalAdvice.html', {})     

def UserScreen(request):
    if request.method == 'GET':
        return render(request, 'UserScreen.html', {})         


def UserLoginAction(request):
    global username
    if request.method == 'POST':
        global username
        status = "none"
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'legal',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username,password FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == users and row[1] == password:
                    username = users
                    status = "success"
                    break
        if status == 'success':
            context= {'data':'Welcome '+username}
            return render(request, "UserScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'UserLogin.html', context)

def RegisterAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
               
        output = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'legal',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    output = username+" Username already exists"
                    break                
        if output == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'legal',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                output = "Signup process completed. Login to perform Legal suggestions"
        context= {'data':output}
        return render(request, 'Register.html', context)        

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})         

def UserLogin(request):
    if request.method == 'GET':
        return render(request, 'UserLogin.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

