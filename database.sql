-- Ejecutar manualmente en una base de datos vacía.
BEGIN;

CREATE TABLE paciente (
    id_paciente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rut VARCHAR(16) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NOT NULL
);

CREATE TABLE medico (
    id_medico INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    especialidad VARCHAR(120) NOT NULL,
    telefono VARCHAR(30) NOT NULL
);

CREATE TABLE atencion (
    id_atencion INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente INTEGER NOT NULL REFERENCES paciente (id_paciente),
    id_medico INTEGER NOT NULL REFERENCES medico (id_medico),
    fecha_atencion DATE NOT NULL,
    fecha_alta DATE,
    diagnostico TEXT NOT NULL,
    costo NUMERIC(12, 2) NOT NULL CHECK (costo >= 0),
    CONSTRAINT fecha_alta_valida CHECK (
        fecha_alta IS NULL OR fecha_alta >= fecha_atencion
    )
);

COMMIT;
