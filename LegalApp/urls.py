from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
	             path("UserLogin.html", views.UserLogin, name="UserLogin"),
		     path("UserLoginAction", views.UserLoginAction, name="UserLoginAction"),
		     path("Register.html", views.Register, name="Register"),
		     path("RegisterAction", views.RegisterAction, name="RegisterAction"),
		     path("LegalAdvice", views.LegalAdvice, name="LegalAdvice"),
		     path("LegalAdviceAction", views.LegalAdviceAction, name="LegalAdviceAction"),
		     path("Chatbot", views.Chatbot, name="Chatbot"),
		     path("Summarize", views.Summarize, name="Summarize"),
		     path("SummarizeAction", views.SummarizeAction, name="SummarizeAction"),
		     path("VoiceChatbot", views.VoiceChatbot, name="VoiceChatbot"),
		     path("ChatData", views.ChatData, name="ChatData"),	
		     path("record", views.record, name="record"),	     
		     path("UserScreen", views.UserScreen, name="UserScreen"),	  
		    ]