import google.generativeai as genai

genai.configure(api_key="AIzaSyBSsK2QKcxYJLmGZB_1mJLJwiTfToLq0rw")

model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content("Say Hello")

print(response.text)