# 1. Importaciones y configuración de Flask
import os
from contextlib import closing
from datetime import date
from decimal import Decimal, InvalidOperation

import psycopg2
from flask import Flask, abort, redirect, render_template, request, url_for
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


#Conexión a PostgreSQL
def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "proyecto_bdd"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
        cursor_factory=RealDictCursor,
    )



@app.errorhandler(psycopg2.Error)
def mostrar_error_de_base(error):
    app.logger.error("Error de PostgreSQL (%s)", error.pgcode or type(error).__name__)
    return render_template(
        "index.html",
        titulo="Base de datos no disponible",
        mensaje="Revisa la conexión a PostgreSQL y que las tres tablas estén creadas.",
    ), 503


@app.errorhandler(404)
def mostrar_pagina_no_encontrada(error):
    return render_template(
        "index.html", titulo="Página no encontrada", mensaje=error.description
    ), 404



@app.get("/")
def inicio():
    return redirect(url_for("pacientes"))


@app.route("/pacientes", methods=["GET", "POST"])
@app.route("/pacientes/<int:id_paciente>/editar", methods=["GET", "POST"])
def pacientes(id_paciente=None):
    formulario = {}
    error = None

    if request.method == "POST":
        formulario = request.form.to_dict()
        rut = formulario.get("rut", "").strip()
        nombre = formulario.get("nombre", "").strip()
        telefono = formulario.get("telefono", "").strip()

        if not rut or not nombre or not telefono:
            error = "Completa el RUT, el nombre y el teléfono."
        elif len(rut) > 16 or len(nombre) > 150 or len(telefono) > 30:
            error = "El RUT, el nombre o el teléfono supera el largo permitido."
        else:
            try:
                with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
                    if id_paciente is None:
                        cursor.execute(
                            "INSERT INTO paciente (rut, nombre, telefono) VALUES (%s, %s, %s)",
                            (rut, nombre, telefono),
                        )
                    else:
                        cursor.execute(
                            """UPDATE paciente SET rut = %s, nombre = %s, telefono = %s
                               WHERE id_paciente = %s""",
                            (rut, nombre, telefono, id_paciente),
                        )
                        if cursor.rowcount == 0:
                            abort(404, "El paciente indicado no existe.")
            except psycopg2.errors.UniqueViolation:
                error = "Ya existe un paciente con ese RUT."
            else:
                return redirect(url_for("pacientes", guardado=1))

    with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
        if id_paciente is not None:
            cursor.execute(
                "SELECT rut, nombre, telefono FROM paciente WHERE id_paciente = %s",
                (id_paciente,),
            )
            paciente = cursor.fetchone()
            if paciente is None:
                abort(404, "El paciente indicado no existe.")
            if request.method == "GET":
                formulario = paciente

        cursor.execute("SELECT id_paciente, rut, nombre, telefono FROM paciente ORDER BY id_paciente")
        registros = cursor.fetchall()

    return render_template(
        "index.html", seccion="pacientes", titulo="Pacientes", registros=registros,
        formulario=formulario, id_edicion=id_paciente, error=error,
    ), 400 if error else 200


@app.route("/medicos", methods=["GET", "POST"])
@app.route("/medicos/<int:id_medico>/editar", methods=["GET", "POST"])
def medicos(id_medico=None):
    formulario = {}
    error = None

    if request.method == "POST":
        formulario = request.form.to_dict()
        nombre = formulario.get("nombre", "").strip()
        especialidad = formulario.get("especialidad", "").strip()
        telefono = formulario.get("telefono", "").strip()

        if not nombre or not especialidad or not telefono:
            error = "Completa el nombre, la especialidad y el teléfono."
        elif len(nombre) > 150 or len(especialidad) > 120 or len(telefono) > 30:
            error = "El nombre, la especialidad o el teléfono supera el largo permitido."
        else:
            with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
                if id_medico is None:
                    cursor.execute(
                        "INSERT INTO medico (nombre, especialidad, telefono) VALUES (%s, %s, %s)",
                        (nombre, especialidad, telefono),
                    )
                else:
                    cursor.execute(
                        """UPDATE medico SET nombre = %s, especialidad = %s, telefono = %s
                           WHERE id_medico = %s""",
                        (nombre, especialidad, telefono, id_medico),
                    )
                    if cursor.rowcount == 0:
                        abort(404, "El médico indicado no existe.")
            return redirect(url_for("medicos", guardado=1))

    with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
        if id_medico is not None:
            cursor.execute(
                "SELECT nombre, especialidad, telefono FROM medico WHERE id_medico = %s",
                (id_medico,),
            )
            medico = cursor.fetchone()
            if medico is None:
                abort(404, "El médico indicado no existe.")
            if request.method == "GET":
                formulario = medico

        cursor.execute("SELECT id_medico, nombre, especialidad, telefono FROM medico ORDER BY id_medico")
        registros = cursor.fetchall()

    return render_template(
        "index.html", seccion="medicos", titulo="Médicos", registros=registros,
        formulario=formulario, id_edicion=id_medico, error=error,
    ), 400 if error else 200


@app.route("/atenciones", methods=["GET", "POST"])
@app.route("/atenciones/<int:id_atencion>/editar", methods=["GET", "POST"])
def atenciones(id_atencion=None):
    formulario = {}
    error = None

    if request.method == "POST":
        formulario = request.form.to_dict()
        try:
            id_paciente = int(formulario.get("id_paciente", ""))
            id_medico = int(formulario.get("id_medico", ""))
            fecha_atencion = date.fromisoformat(formulario.get("fecha_atencion", ""))
            alta = formulario.get("fecha_alta", "")
            # psycopg2 envía None como NULL en PostgreSQL.
            fecha_alta = date.fromisoformat(alta) if alta else None
            diagnostico = formulario.get("diagnostico", "").strip()
            costo = Decimal(formulario.get("costo", ""))
        except (ValueError, InvalidOperation):
            error = "Selecciona un paciente y un médico e ingresa fechas y costo válidos."
        else:
            if not diagnostico:
                error = "Ingresa el diagnóstico."
            elif fecha_alta is not None and fecha_alta < fecha_atencion:
                error = "La fecha de alta debe ser igual o posterior a la fecha de atención."
            elif (
                not costo.is_finite() or not 0 <= costo <= Decimal("9999999999.99")
                or costo != costo.quantize(Decimal("0.01"))
            ):
                error = "Ingresa un costo entre 0 y 9.999.999.999,99 con hasta dos decimales."

        if error is None:
            datos = (id_paciente, id_medico, fecha_atencion, fecha_alta, diagnostico, costo)
            try:
                with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
                    if id_atencion is None:
                        cursor.execute(
                            """INSERT INTO atencion
                               (id_paciente, id_medico, fecha_atencion, fecha_alta, diagnostico, costo)
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            datos,
                        )
                    else:
                        cursor.execute(
                            """UPDATE atencion
                               SET id_paciente = %s, id_medico = %s, fecha_atencion = %s,
                                   fecha_alta = %s, diagnostico = %s, costo = %s
                               WHERE id_atencion = %s""",
                            datos + (id_atencion,),
                        )
                        if cursor.rowcount == 0:
                            abort(404, "La atención indicada no existe.")
            except (psycopg2.errors.ForeignKeyViolation, psycopg2.errors.NumericValueOutOfRange):
                error = "Selecciona un paciente y un médico registrados."
            else:
                return redirect(url_for("atenciones", guardado=1))

    with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
        if id_atencion is not None:
            cursor.execute(
                """SELECT id_paciente, id_medico, fecha_atencion, fecha_alta, diagnostico, costo
                   FROM atencion WHERE id_atencion = %s""",
                (id_atencion,),
            )
            atencion = cursor.fetchone()
            if atencion is None:
                abort(404, "La atención indicada no existe.")
            if request.method == "GET":
                formulario = atencion

        cursor.execute("SELECT id_paciente, nombre, rut FROM paciente ORDER BY nombre, id_paciente")
        opciones_pacientes = cursor.fetchall()
        cursor.execute("SELECT id_medico, nombre, especialidad FROM medico ORDER BY nombre, id_medico")
        opciones_medicos = cursor.fetchall()

        cursor.execute(
            """SELECT a.id_atencion, a.id_paciente, p.nombre AS paciente,
                      a.id_medico, m.nombre AS medico, a.fecha_atencion,
                      a.fecha_alta, a.diagnostico, a.costo
               FROM atencion AS a
               JOIN paciente AS p ON p.id_paciente = a.id_paciente
               JOIN medico AS m ON m.id_medico = a.id_medico
               ORDER BY a.id_atencion"""
        )
        registros = cursor.fetchall()

    return render_template(
        "index.html", seccion="atenciones", titulo="Atenciones", registros=registros,
        formulario=formulario, id_edicion=id_atencion, error=error,
        opciones_pacientes=opciones_pacientes, opciones_medicos=opciones_medicos,
    ), 400 if error else 200


@app.get("/atenciones-vigentes")
def atenciones_vigentes():
    with closing(conectar()) as conexion, conexion, conexion.cursor() as cursor:
        cursor.execute(
            """SELECT p.nombre AS paciente, m.nombre AS medico, m.especialidad
               FROM atencion AS a
               JOIN paciente AS p ON p.id_paciente = a.id_paciente
               JOIN medico AS m ON m.id_medico = a.id_medico
               WHERE a.fecha_alta IS NULL
               ORDER BY a.id_atencion"""
        )
        registros = cursor.fetchall()

    return render_template(
        "index.html", seccion="vigentes", titulo="Atenciones vigentes", registros=registros
    )


# 7. Inicio de la aplicación
if __name__ == "__main__":
    app.run()
