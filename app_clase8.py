from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from person import Person
from client import Client
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user_api_flask'
app.config['MYSQL_PASSWORD'] = '32978644'
app.config['MYSQL_DB'] = 'db_api_flask'
app.config['SECRET_KEY'] = 'app_123'

mysql = MySQL(app)

# Ruta principal de la API
@app.route('/')
def index():
    """Ruta de inicio que devuelve un mensaje JSON."""
    return jsonify({"message": "API desarrollada con Flask"})

# Ruta para la autenticación y generación de tokens JWT
@app.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticación y generación de tokens JWT."""
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return jsonify({"message": "No autorizado"}), 401
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (auth.username, auth.password))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"message": "No autorizado"}), 401
    
    # Generar un token JWT válido por 5 minutos
    token = jwt.encode({'id': row[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
    return jsonify({"token": token, "user": auth.username, "id": row[0]})

# Decorador para verificar la validez del token JWT
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({"message": "falta el token"}), 401
        
        user_id = None
        if 'user-id' in request.headers:
            user_id = request.headers['user-id']
        if not user_id:
            return jsonify({"message": "Falta el usuario"}),401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            token_id = data['id']
            if (user_id) != int(token_id):
                return jsonify({"message": "Error de id"})
        except Exception as e:
            print(e)
            return jsonify({"message": str(e)}), 401
        return func(*args, **kwargs)
    return decorated

# Ruta protegida por autenticación mediante token JWT
@app.route('/test/<int:id>')
#@token_required
def test(id):
    """Ejemplo de ruta protegida por token JWT."""
    return jsonify({"message": "funcion test"})

# Ruta para obtener todas las personas desde la base de datos
@app.route('/persons', methods=['GET'])
def get_all_persons():
    """Obtiene todas las personas desde la base de datos."""
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM person')
    data = cur.fetchall()
    listPerson = []
    for row in data:
        objectPerson = Person(row)
        listPerson.append(objectPerson.to_json())
    return jsonify(listPerson)

# Ruta para crear una nueva persona en la base de datos
@app.route('/persons', methods=['POST'])
def create_persons():
    """Crea una nueva persona en la base de datos."""
    name = request.get_json()["name"]
    surname = request.get_json()["surname"]
    dni = request.get_json()["dni"]
    email = request.get_json()["email"]
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM person WHERE email=%s', (email,))
    row = cur.fetchone()
    
    if row:
        return jsonify({"message": "email ya registrado"})
    
    cur.execute('INSERT INTO person(name, surname, dni, email) VALUES (%s,%s,%s,%s )', (name, surname, dni, email))
    mysql.connection.commit()
    
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    id = row[0]
    return jsonify({"name": name, "surname": surname, "dni": dni, "email": email, "id": id})

# Ruta para obtener una persona por su ID
@app.route('/persons/<int:id>', methods=['GET'])
def get_person_by_id(id):
    """Obtiene una persona desde la base de datos por su ID."""
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM person WHERE id= {0}'.format(id))
    data = cur.fetchall()
    if cur.rowcount > 0:
        objectPerson = Person(data[0])
        return jsonify(objectPerson.to_json())
    return jsonify({"message": "id not found"})

# Ruta para actualizar una persona por su ID
@app.route('/persons/<int:id>', methods=['PUT'])
def update_person(id):
    """Actualiza una persona en la base de datos por su ID."""
    name = request.get_json()["name"]
    surname = request.get_json()["surname"]
    dni = request.get_json()["dni"]
    email = request.get_json()["email"]
    
    cur = mysql.connection.cursor()
    cur.execute('UPDATE  person SET name =%s, surname=%s, dni = %s, email=%s WHERE id =%s', (name, surname, dni, email, id))
    mysql.connection.commit()
    
    return jsonify({"id": id, "name": name, "surname": surname, "dni": dni, "email": email})

# Ruta para eliminar una persona por su ID
@app.route('/persons/<int:id>', methods=['DELETE'])
def remove_person(id):
    """Elimina una persona desde la base de datos por su ID."""
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM person WHERE id= {0}'.format(id))
    mysql.connection.commit()
    return jsonify({"message": "delete", "id": id})


# Ruta para obtener una cliente por su ID
@app.route('/client/<int:id>', methods=['GET'])
#@token_required
def get_client_by_id(id):
    """Obtiene una persona desde la base de datos por su ID."""
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client WHERE id= {0}'.format(id))
    data = cur.fetchall()
    if cur.rowcount > 0:
        objectClient = Client(data[0])
        return jsonify(objectClient.to_json())
    return jsonify({"message": "id not found"})




if __name__ == '__main__':
    app.run(debug=True, port=4500)
