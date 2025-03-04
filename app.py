from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import pickle
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration for file uploads
UPLOAD_FOLDER = r"C:\Users\user\Downloads\Biogas_frontend_Graph_new (2)\Biogas_frontend_Graph_new (1)\Biogas_frontend_Graph_new"
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  

# Dummy user class (replace with a real user model)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Dummy user credentials 
USERNAME = "admin"
PASSWORD = "password123"

# Load the trained model and dataset
model = pickle.load(open('new_best_model_XGBoost.pkl', 'rb'))

# Load the dataset if it exists, otherwise create an empty DataFrame
try:
    df = pd.read_csv('new_biogas_dataframe.csv')
except:
    # Create an empty DataFrame with required columns if file doesn't exist
    df = pd.DataFrame(columns=['date', 'waste_smc', 'msw_rec', 'dig_feed', 'dig_feed_1', 'disposal_A',
                              'disposal_B', 'dig_press', 'dig_level', 'balloon_a', 'balloon_b',
                              'engine_running_hrs', 'total_power_gene', 'export_power',
                              'gas_consumption', 'sfc', 'raw_msw_TS', 'raw_msw_VS', 'raw_msw_MC',
                              'ac_02_TS', 'ac_02_VS', 'ac_02_MC', 'ac_02_sand', 'ac_02_CN',
                              'ac_02_cod'])

# Required columns for validation
REQUIRED_COLUMNS = [
    "date", "waste_smc", "msw_rec", "dig_feed", "dig_feed_1", "disposal_A", "disposal_B", "dig_press",
    "dig_level", "balloon_a", "balloon_b", "engine_running_hrs", "total_power_gene", "export_power",
    "gas_consumption", "sfc", "raw_msw_TS", "raw_msw_VS", "raw_msw_MC", "ac_02_TS", "ac_02_VS",
    "ac_02_MC", "ac_02_sand", "ac_02_CN", "ac_02_cod", "digester_feed_TS", "digester_feed_VS",
    "digester_feed_MC", "digester_feed_PH", "digester_feed_VFA", "digester_feed_ALK",
    "digester_feed_VA", "digester_feed_EC", "digester_feed_Temp", "digester_feed_COD",
    "digester_recycle_TS", "digester_recycle_VS", "digester_recycle_MC", "digester_recycle_PH",
    "digester_recycle_VFA", "digester_recycle_ALK", "digester_recycle_VA", "digester_recycle_EC",
    "digester_recycle_Temp", "digester_recycle_TOC", "digester_disposal_TS", "digester_disposal_VS",
    "digester_disposal_MC", "digester_disposal_PH", "digester_disposal_VFA", "digester_disposal_ALK",
    "digester_disposal_VA", "digester_disposal_EC", "digester_disposal_Temp", "digester_disposal_TOC",
    "biogas_clean_Methane%", "biogas_clean_H2S(ppm)", "biogas_clean_Clean Biogas Methane%",
    "biogas_clean_Clean Biogas H2S(ppm)", "biogas_clean_Dosing pH", "biogas_clean_Scrubber pH"
]

# Function to get values by date
def get_values_by_date(df, date):
    required_columns = [
        'waste_smc', 'msw_rec', 'dig_feed', 'dig_feed_1', 'disposal_A',
        'disposal_B', 'dig_press', 'dig_level', 'balloon_a', 'balloon_b',
        'engine_running_hrs', 'total_power_gene', 'export_power',
        'gas_consumption', 'sfc', 'raw_msw_TS', 'raw_msw_VS', 'raw_msw_MC',
        'ac_02_TS', 'ac_02_VS', 'ac_02_MC', 'ac_02_sand', 'ac_02_CN',
        'ac_02_cod'
    ]

    df['date'] = pd.to_datetime(df['date'])
    data_for_date = df[df['date'] == pd.to_datetime(date)][required_columns]
    return data_for_date.values

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            user = User(1)  # Create a user object (replace with real user logic)
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main'))
        else:
            flash('Invalid credentials, please try again.', 'error')
    return render_template('login.html')

@app.route('/dataset')
def dataset():
    return render_template('dataset.html')

@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    global df
    
    if 'dataset' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['dataset']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save the uploaded file
            file.save(filepath)
            
            # Try to load the new dataset to validate it
            new_df = pd.read_csv(filepath)
            
            # Check if the uploaded file has the required columns
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in new_df.columns]
            
            if missing_columns:
                os.remove(filepath)  # Remove the invalid file
                if len(missing_columns) > 3:
                    message = f'Dataset validation failed: Missing {len(missing_columns)} required columns. Please check the dataset format.'
                else:
                    message = f'Dataset validation failed: Missing columns [{", ".join(missing_columns[:3])}{"..." if len(missing_columns) > 3 else ""}]'
                return jsonify({
                    'success': False, 
                    'message': message
                })
            
            # If all validation passes, update the global dataframe
            df = new_df
            
            # Save as the main dataset file
            df.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'new_biogas_dataframe.csv'), index=False)
            
            return jsonify({
                'success': True, 
                'message': 'Dataset uploaded and saved successfully!'
            })
            
        except Exception as e:
            # If there was an error processing the file, remove it
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': False, 
                'message': 'Dataset validation failed: The file format appears to be incorrect or corrupted.'
            })
    
    return jsonify({
        'success': False, 
        'message': 'Invalid file format. Please upload a CSV file.'
    })


# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Route for main page (protected)
@app.route('/main')
@login_required
def main():
    return render_template('main.html')

# Route for dashboard (protected)
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        date = request.form.get('date')
        try:
            input_data = get_values_by_date(df, date)
            if input_data.size == 0:
                return jsonify({'error': 'No data found for the selected date.'})
            prediction = model.predict(input_data)
            return jsonify({'prediction': prediction.tolist()})
        except Exception as e:
            return jsonify({'error': str(e)})
    return render_template('dashboard.html')

# Function to get feature values
def get_feature_values(df, feature, current_date):
    current_date = pd.to_datetime(current_date)
    df['date'] = pd.to_datetime(df['date'])
    
    past_values = df[(df['date'] < current_date) & (df['date'] >= current_date - pd.Timedelta(days=15))][['date', feature]]
    current_value = df[df['date'] == current_date][['date', feature]]
    future_values = df[(df['date'] > current_date) & (df['date'] <= current_date + pd.Timedelta(days=7))][['date', feature]]
    
    return past_values, current_value, future_values

# Route for graph (protected)
@app.route('/graph')
@login_required
def graph():
    graph_name = request.args.get('name')  # Get featureName from query params
    graph_date = request.args.get('date')  # Get date from query params
    main_feature = request.args.get("main_feature")
    feature_name = main_feature + "_" + graph_name
    past, current, future = get_feature_values(df, feature_name, graph_date)
    past_15_days = past[feature_name].tolist()
    current_value = current[feature_name].tolist()
    future_7_days = future[feature_name].tolist()
    print("past 15 days", past_15_days, "current", current_value, "future 7 days", future_7_days)
    
    return render_template('test.html', 
                           graph_date=graph_date, 
                           graph_name=graph_name,
                           past_15_days=past_15_days,
                           current_value=current_value,
                           future_7_days=future_7_days)

if __name__ == '__main__':
    app.run(debug=True)