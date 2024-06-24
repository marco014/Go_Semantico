from flask import Flask, request, render_template
import os
import re

app = Flask(__name__)
carpeta_subida = 'uploads/'
if not os.path.exists(carpeta_subida):
    os.makedirs(carpeta_subida)
app.config['carpeta_subida'] = carpeta_subida

def analisis_lexico(codigo):
    resultado = []
    palabras_clave = {'package', 'import', 'func', 'var', 'const', 'type', 'struct', 'interface', 'if', 'else', 'switch', 'case', 'default', 'for', 'range', 'go', 'select', 'defer', 'map', 'chan', 'return', 'break', 'continue', 'goto', 'fallthrough', 'defer', 'panic', 'recover'}  # Palabras reservadas de Go
    lineas = codigo.split('\n')
    for numero_linea, linea in enumerate(lineas, start=1):
        indice = 0
        while indice < len(linea):
            token_detectado = False
            for palabra in palabras_clave:
                if linea[indice:].startswith(palabra) and (indice + len(palabra) == len(linea) or not linea[indice + len(palabra)].isalnum()):
                    resultado.append((numero_linea, indice, 'Palabra reservada', palabra))
                    indice += len(palabra)
                    token_detectado = True
                    break
            if token_detectado:
                continue

            caracter = linea[indice]
            if caracter in [';', '{', '}', '(', ')', '[', ']', '*', '&', '|', '^', '!', '<', '>', '=', '+', '-', '/', '%', ':', '.', ',']:
                tipo = 'Símbolo'
                resultado.append((numero_linea, indice, tipo, caracter))
                indice += 1
            elif caracter.isdigit():
                resultado.append((numero_linea, indice, 'Número', caracter))
                indice += 1
            else:
                indice += 1
    return resultado

def analisis_sintactico(codigo):
    resultado = []
    palabras_clave = {'package', 'import', 'func', 'main'}  # Palabras reservadas de Go para la sintaxis
    lineas = codigo.split('\n')
    for numero_linea, linea in enumerate(lineas, start=1):
        linea_sin_espacios = linea.strip()
        tokens = linea_sin_espacios.split()
        for token in tokens:
            if token in palabras_clave:
                resultado.append((numero_linea, token.capitalize(), True))
            elif any(palabra in token for palabra in palabras_clave):
                # Añade una comprobación para 'main()'
                if token == 'main()':
                    resultado.append((numero_linea, token.capitalize(), True))
                else:
                    resultado.append((numero_linea, token.capitalize(), False))
                break
    return resultado

def analisis_semantico(codigo):
    resultado = []
    variables = {}
    lineas = codigo.split('\n')
    
    for numero_linea, linea in enumerate(lineas, start=1):
        tokens = re.findall(r'\b\w+\b', linea)
        if 'var' in tokens or 'const' in tokens:
            if tokens[1] in variables:
                resultado.append((numero_linea, f"Error: La variable '{tokens[1]}' ya está declarada."))
            else:
                variables[tokens[1]] = True
        elif '=' in tokens:
            if tokens[0] not in variables:
                resultado.append((numero_linea, f"Error: La variable '{tokens[0]}' no está declarada."))
    
    return resultado

@app.route('/', methods=['GET', 'POST'])
def inicio():
    codigo = ""
    resultado_lexico = []
    resultado_sintactico = []
    resultado_semantico = []
    if request.method == 'POST':
        if request.form.get('action') == 'Ejecutar':
            if 'file' in request.files and request.files['file'].filename != '':
                archivo = request.files['file']
                ruta_archivo = os.path.join(app.config['carpeta_subida'], archivo.filename)
                archivo.save(ruta_archivo)
                with open(ruta_archivo, 'r') as f:
                    codigo = f.read()
            elif 'code' in request.form and request.form['code'].strip() != '':
                codigo = request.form['code']
            else:
                return "No se seleccionó ningún archivo o no se proporcionó código"
            
            resultado_lexico = analisis_lexico(codigo)
            resultado_sintactico = analisis_sintactico(codigo)
            resultado_semantico = analisis_semantico(codigo)
        elif request.form.get('action') == 'Borrar':
            codigo = ""
            resultado_lexico = []
            resultado_sintactico = []
            resultado_semantico = []
        
    return render_template('index.html', codigo=codigo, resultado_lexico=resultado_lexico, resultado_sintactico=resultado_sintactico, resultado_semantico=resultado_semantico)

if __name__ == '__main__':
    app.run(debug=True)
