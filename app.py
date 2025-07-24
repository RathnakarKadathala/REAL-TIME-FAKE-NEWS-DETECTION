from flask import Flask, render_template, request, jsonify, redirect, url_for
import nltk
import pickle
from nltk.corpus import stopwords
import re
from nltk.stem.porter import PorterStemmer
from flask import Flask, render_template, request, redirect, url_for, session
#from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



from flask import Flask, request, jsonify
from flask_pymongo import PyMongo


from pymongo import MongoClient

# Replace <username>, <password>, and <cluster-url> with your details
client = MongoClient("mongodb+srv://pavaniyadav926:123%40pro@cluster0.vg5nj.mongodb.net/fakenewsdetection?retryWrites=true&w=majority")
db = client["fakenewsdetection"]  # Use your database name

app = Flask(__name__)
app.secret_key = 'fc2125b73bbe354a9516894dd0e4adb2'
# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://pavaniyadav926:123%40pro@cluster0.vg5nj.mongodb.net/fakenewsdetection?retryWrites=true&w=majority"
# Initialize PyMongo
mongo = PyMongo(app)

# Collections
users_collection = mongo.db.users
search_history_collection = db['search_data']  


#@app.route("/register", methods=["POST"])
#def register():
 #   data = request.json
  #  users_collection.insert_one({
   #     "name": data.get("name"),
    #    "email": data.get("email"),
     #   "password": data.get("password")
    #})
    #return jsonify({"message": "User registered successfully!"}), 201

#@app.route("/search", methods=["POST"])
#def search():
 #   data = request.json
  #  searches_collection.insert_one({
   #     "user_email": data.get("email"),
    #    "search_query": data.get("query")
    #})
    #return jsonify({"message": "Search query stored successfully!"}), 201

@app.route('/search', methods=['POST'])
def search():
    if 'user_id' in session:
        user_id = session['user_id']
        search_query = request.form['search_query']

        # Save search query to the database
        mongo.db.search_history.insert_one({
            'user_id': user_id,
            'search_query': search_query,
            'timestamp': datetime.datetime.now()
        })

        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in
@app.route('/search_history')
def search_history():
    # Fetch data with the correct field names
    search_history = list(search_history_collection.find(
        {}, 
        {"_id": 0, "query": 1, "prediction": 1, "timestamp": 1}
    ))

    # Debugging: Print the search history to check what is being fetched
    print(search_history)
    
    return render_template('search_history.html', search_history=search_history)

#app = Flask(__name__)
ps = PorterStemmer()

# Load the pre-trained model and TF-IDF vectorizer
model = pickle.load(open('model2.pkl', 'rb'))
tfidfvect = pickle.load(open('tfidfvect2.pkl', 'rb'))

# Function to preprocess text and predict
def predict(text):
    review = re.sub('[^a-zA-Z]', ' ', text)  # Remove non-alphabetic characters
    review = review.lower()  # Convert to lowercase
    review = review.split()  # Tokenize
    review = [ps.stem(word) for word in review if word not in stopwords.words('english')]  # Remove stopwords and stem
    review = ' '.join(review)  # Join the words back
    review_vect = tfidfvect.transform([review]).toarray()  # Vectorize input
    prediction = 'FAKE' if model.predict(review_vect) == 0 else 'REAL'  # Predict
    return prediction

# Route: Home Page
#@app.route('/', methods=['GET', 'POST'])
#def home():
 #   if request.method == 'POST':
  #      text = request.form.get('text')  # Safely fetch the input
   #     if text:  # Ensure input is not empty
    #        prediction = predict(text)
     #       return render_template('index.html', text=text, result=prediction)
    #return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        # User is logged in, fetch user details
        user = mongo.db.users.find_one({'_id': session['user_id']})
        return render_template('home.html', user=user)
    else:
        # Redirect to login if not logged in
         redirect(url_for('login'))
    if request.method == 'POST':
        text = request.form.get('text')  # Get user input
        if text:  # Check if input is not empty
            prediction = predict(text)  # Use your prediction logic

            # Store search data in MongoDB
            search_collection = db["search_data"]  # Create/use a collection named "search_data"
            search_document = {
                "query": text,
                "prediction": prediction,
                "timestamp": datetime.now()
            }
            search_collection.insert_one(search_document)  # Insert the document

            return render_template('index.html', text=text, result=prediction)
    return render_template('index.html')


# Route: About Page
@app.route('/about', methods=['GET'])
def about():
    return render_template('aboutus.html')

# Route: Contact Page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:  # Ensure the message is not empty
            # You can add functionality to store or process the message
            return render_template('contactus.html', success=True, message=user_message)
    return render_template('contactus.html')
@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    
    # Here you can handle the form data, such as sending an email or saving to a database
    return "Thank you for contacting us!"
#Rout:Register


# Dummy data for storing registered users (In real applications, this should be a database)
users = []

# Route for displaying the register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([name, email, password, confirm_password]):
            return "All fields are required!", 400

        if password != confirm_password:
            return "Passwords do not match!", 400

        # Save user data to MongoDB
        user = {"name": name, "email": email, "password": password}
        mongo.db.users.insert_one(user)

        return redirect('/login')
    return render_template('register.html')

# Route: Login Page
@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))  # If the user is already logged in, redirect to home.

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user from DB to verify credentials
        user = mongo.db.users.find_one({'username': username, 'password': password})

        if user:
            # Store user ID in session after successful login
            session['user_id'] = str(user['_id'])  # Store as string to avoid BSON ObjectID issues
            return redirect(url_for('home'))  # Redirect to home page
        else:
            error = 'Invalid credentials'
            return render_template('login.html', error=error)
    
    return render_template('login.html')


# API Route: Predict Fake News
@app.route('/predict/', methods=['GET'])
def api():
    text = request.args.get("text")
    if text:  # Ensure text parameter is provided
        prediction = predict(text)
        return jsonify(prediction=prediction)
    return jsonify(error="No text provided"), 400

# Main Function
if __name__ == "__main__":
    app.run(debug=True)
