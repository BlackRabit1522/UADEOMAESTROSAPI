from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import OperationalError
from config import Config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config.from_object(Config)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

def get_db_connection():
    """Establece la conexión a la base de datos PostgreSQL."""
    try:
        connection = psycopg2.connect(
            host=app.config['POSTGRES_HOST'],
            user=app.config['POSTGRES_USER'],
            password=app.config['POSTGRES_PASSWORD'],
            dbname=app.config['POSTGRES_DATABASE']
        )
        return connection
    except OperationalError as e:
        print(f"Error al conectar a PostgreSQL: {e}")
        return None

# Ruta para el login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Faltan datos"}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM maestros WHERE correo = %s AND contraseña = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        access_token = create_access_token(identity=user[0])  # Asumiendo que el ID es el primer campo
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

# Ruta para obtener todos los registros de maestros
@app.route('/api/maestros', methods=['GET'])
@jwt_required()
def get_maestros():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM maestros")
    registros = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(registros)

# Ruta para obtener todos los registros de alumnos
@app.route('/api/alumnos', methods=['GET'])
@jwt_required()
def get_alumnos():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM alumnos")
    registros = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(registros)

# Ruta para agregar un nuevo registro de Actividades
@app.route('/api/<int:id_maestro>/registro', methods=['POST'])
@jwt_required()
def obtener_alumnos_id_materia(id_maestro):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    descripcion = data.get('descripcion')

    if not descripcion:
        return jsonify({"error": "Faltan datos"}), 400

    # Verificar si el ID del maestro en el token coincide con el ID del maestro en la URL
    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor()
    cursor.execute("SELECT id FROM materias WHERE id_maestro = %s", (id_maestro,))
    id_materia = cursor.fetchone()
    if not id_materia:
        return jsonify({"error": "Materia no encontrada"}), 404

    id_materia = id_materia[0]
    cursor.execute(
        "INSERT INTO actividades (id_materia_act, descripcion) VALUES (%s, %s)",
        (id_materia, descripcion)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Actividad registrada con éxito"}), 200


# Ruta para vincular actividades a los alumnos
@app.route('/api/<int:id_maestro>/alumnos/actividades', methods=['POST'])
@jwt_required()
def Vincular_actividades(id_maestro):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    id_alumno = data.get('id_alumno')
    calificacion = data.get('calificacion')
    id_actividad = data.get('id_actividad')

    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    # Conexión a la base de datos
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    if not id_alumno or not calificacion or not id_actividad:
        return jsonify({"error": "Faltan datos"}), 400

    cursor = connection.cursor()

    cursor.execute("SELECT id FROM materias WHERE id_maestro = %s", (id_maestro,))
    materia_result = cursor.fetchone()

    if not materia_result:
        return jsonify({"error": "Materia no encontrada para el maestro"}), 404

    cursor.execute("""
        INSERT INTO alumno_has_actividades (id_actividad, id_alumno_act, calificacionActividad)
        VALUES (%s, %s, %s)
        ON CONFLICT (id_actividad, id_alumno_act) DO UPDATE SET calificacionActividad = EXCLUDED.calificacionActividad
    """, (id_actividad, id_alumno, calificacion))

    connection.commit()

    return jsonify({"exito": "Datos Añadidos o Actualizados"}), 200


# Registrar un nuevo alumno en la base de datos
@app.route('/api/<int:id_maestro>/ingresar/alumno', methods=['POST'])
@jwt_required()
def obtener_datos_alumno(id_maestro):
    current_user_id = get_jwt_identity()
    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    data = request.get_json()
    nom_alumno = data.get('alumno')

    if not nom_alumno or not isinstance(nom_alumno, str):
        return jsonify({"error": "Nombre del alumno es obligatorio y debe ser una cadena de texto válida"}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO alumnos (nombre) VALUES (%s)", (nom_alumno,))
        connection.commit()
        cursor.close()
        return jsonify({"message": "Alumno agregado con éxito"}), 201

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Hubo un error al intentar agregar al alumno"}), 500

    finally:
        connection.close()

# Eliminar alumno de la base de datos
@app.route('/api/<int:id_maestro>/eliminar/alumno/<int:id_alumno>', methods=['DELETE'])
@jwt_required()
def eliminar_alumno(id_maestro, id_alumno):
    current_user_id = get_jwt_identity()
    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE id = %s", (id_alumno,))
        alumno = cursor.fetchone()

        if not alumno:
            return jsonify({"error": "Alumno no encontrado"}), 404

        cursor.execute("DELETE FROM alumnos WHERE id = %s", (id_alumno,))
        connection.commit()

        cursor.close()
        return jsonify({"message": "Alumno eliminado con éxito"}), 200

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Hubo un error al intentar eliminar al alumno"}), 500

    finally:
        connection.close()

# Obtener alumnos por materia
@app.route('/api/materias/<int:id_maestro>/alumnos', methods=['GET'])
@jwt_required()
def obtener_alumnos_por_materia(id_maestro):
    current_user_id = get_jwt_identity()

    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor()
    cursor.execute("""
        SELECT a.id AS alumno_id, a.nombre AS alumno_nombre
        FROM alumnos a
        JOIN alumno_has_materias am ON a.id = am.id_alumno_mat
        WHERE am.id_materia_mat IN (SELECT id FROM materias WHERE id_maestro = %s)
    """, (id_maestro,))
    alumnos = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(alumnos)


@app.route('/api/calificaciones/<int:id_maestro>/calificar', methods=['POST'])
@jwt_required()
def registrar_calificacion(id_maestro):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # Obtener datos del cuerpo de la solicitud
    id_alumno = data.get('alumno')
    id_materia = data.get('materia')
    participacion = data.get('participacion', 0)
    tarea_entregada = data.get('tarea', 0)

    # Validación de datos
    if not id_alumno or not id_materia:
        return jsonify({"error": "Faltan datos esenciales: alumno o materia"}), 400
    if not isinstance(id_alumno, int) or not isinstance(id_materia, int):
        return jsonify({"error": "El id del alumno y de la materia deben ser enteros"}), 400
    if participacion not in [0, 1] or tarea_entregada not in [0, 1]:
        return jsonify({"error": "Valores inválidos para 'participacion' o 'tarea'. Deben ser 0 o 1"}), 400
    if current_user_id != id_maestro:
        return jsonify({"error": "Acción no permitida"}), 403

    # Establecer conexión con la base de datos
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()

        # Verificar la asistencia del alumno en la materia
        cursor.execute("""
            SELECT asistencia FROM asistencias
            WHERE id_materia = %s AND id_alumno = %s ORDER BY fecha DESC LIMIT 1
        """, (id_materia, id_alumno))
        asistencia = cursor.fetchone()

        # Calcular el promedio de las calificaciones de las actividades
        cursor.execute("""
            SELECT AVG(calificacionActividad) FROM alumno_has_actividades
            WHERE id_alumno_act = %s
            AND id_actividad IN (SELECT id_materia_act FROM actividades WHERE id_materia_act = %s)
        """, (id_alumno, id_materia))
        calificacion_actividades = cursor.fetchone()[0] or 0

        # Definir los puntos para cada aspecto de la calificación
        CALIFICACION_BASE = 5
        PUNTOS_ASISTENCIA = 3
        PUNTOS_PARTICIPACION = 2
        PUNTOS_TAREA = 3
        PUNTOS_ACTIVIDADES = 2

        # Calcular la calificación total
        calificacion_total = CALIFICACION_BASE
        if asistencia and asistencia[0] == 1:
            calificacion_total += PUNTOS_ASISTENCIA
        if participacion == 1:
            calificacion_total += PUNTOS_PARTICIPACION
        if tarea_entregada == 1:
            calificacion_total += PUNTOS_TAREA
        calificacion_total += calificacion_actividades * PUNTOS_ACTIVIDADES

        # Limitar la calificación entre 5 y 10
        calificacion_total = max(5, min(calificacion_total, 10))

        # Insertar o actualizar la calificación en la tabla alumno_has_materias
        cursor.execute("""
            INSERT INTO alumno_has_materias (id_materia_mat, id_alumno_mat, calificacionMateria)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_materia_mat, id_alumno_mat) 
            DO UPDATE SET calificacionMateria = EXCLUDED.calificacionMateria
        """, (id_materia, id_alumno, calificacion_total))

        connection.commit()

        # Responder con la calificación registrada
        return jsonify({
            "message": "Calificación registrada correctamente",
            "calificacion": calificacion_total,
            "alumno": id_alumno,
            "materia": id_materia
        }), 200

    except Exception as e:
        app.logger.error(f"Error al registrar calificación: {str(e)}")
        return jsonify({"error": "Ocurrió un error al registrar la calificación"}), 500

    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
