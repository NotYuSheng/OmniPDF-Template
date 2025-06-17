## 🐳 Docker Commands

-```docker build -f chat_service/Dockerfile -t chat-service . --debug```
-```docker run --env-file ./chat_service/.env -d -p 8000:8000 chat-service```


## 🚀 Development Mode

-```uvicorn main:app --reload```