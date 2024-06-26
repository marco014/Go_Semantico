from flask import Flask, request, render_template_string
import re
import ply.lex as lex

app = Flask(__name__)

# Definición de tokens para el analizador léxico
tokens = [
    'KEYWORD', 'ID', 'NUM', 'SYM', 'STRING', 'ERR'
]

t_KEYWORD = r'\b(package|import|func|main|for|if|else|return|fmt|Println|string|int)\b'
t_ID = r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
t_NUM = r'\b\d+\b'
t_SYM = r'[;{}()\[\]=<>!+-/*]'
t_STRING = r'\".*?\"'
t_ERR = r'.'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Plantilla HTML para mostrar resultados
html_template = '''
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #222831;
        color: #eaeaea;
        margin: 0;
        padding: 20px;
    }
    h1 {
        text-align: center;
        color: #ff5722; /* Neón naranja */
    }
    h2 {
        color: #ff5722; /* Neón naranja */
    }
    form {
        margin-bottom: 20px;
        background-color: #393e46;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center; /* Centrar contenido del formulario */
    }
    form label {
        display: block;
        margin-bottom: 8px;
        color: #c5c6c7;
    }
    form textarea,
    form input[type="submit"] {
        padding: 10px;
        margin-bottom: 10px;
        border: none;
        border-radius: 20px;
        box-sizing: border-box;
    }
    form textarea {
        background-color: #222831;
        color: #eaeaea;
        border: 2px solid #ff5722; /* Neón naranja */
        transition: border-color 0.3s;
        width: 80%; /* Ajuste del ancho del cuadro de texto */
        height: 150px; /* Ajuste de la altura del cuadro de texto */
        margin: 0 auto; /* Centrando el cuadro de texto */
    }
    form textarea:focus {
        border-color: #ff784e; /* Neón naranja más claro */
    }
    form input[type="submit"] {
        background-color: #ff5722; /* Neón naranja */
        color: #fff;
        cursor: pointer;
        transition: background-color 0.3s;
        width: 200px; /* Ajuste del ancho del botón */
        margin: 0 auto; /* Centrando el botón */
        display: block; /* Para centrar el botón */
    }
    form input[type="submit"]:hover {
        background-color: #ff784e; /* Neón naranja más claro */
    }
    .table-container {
        display: flex;
        justify-content: center;
        gap: 20px;
    }
    table {
        width: 100%;
        max-width: 500px;
        border-collapse: collapse;
        margin-bottom: 20px;
        background-color: #393e46;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    table th, table td {
        border: 1px solid #ff5722; /* Neón naranja */
        padding: 10px;
        text-align: left;
        color: #eaeaea;
    }
    th {
        background-color: #ff5722; /* Neón naranja */
        color: #fff;
    }
    tr:nth-child(even) {
        background-color: #222831;
    }
    tr td:first-child,
    tr th:first-child {
        border-radius: 8px 0 0 8px;
    }
    tr td:last-child,
    tr th:last-child {
        border-radius: 0 8px 8px 0;
    }
    .error {
        color: #ff3b3b; /* Neón rojo */
    }
  </style>
  <title>Analizador Go</title>
</head>
<body>
  <h1>Analizador Go</h1>
  <form method="post">
    <label for="code">Ingresa el código aquí:</label><br>
    <textarea name="code" rows="10" cols="50">{{ code }}</textarea><br><br>
    <input type="submit" value="Analizar">
  </form>
  <div class="table-container">
    {% if lexical %}
    <div>
      <h2>Analizador Léxico</h2>
      <table>
        <tr>
          <th>Tokens</th><th>KEYWORD</th><th>ID</th><th>Números</th><th>Símbolos</th><th>Error</th>
        </tr>
        {% for row in lexical %}
        <tr>
          <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td><td>{{ row[4] }}</td><td>{{ row[5] }}</td>
        </tr>
        {% endfor %}
        <tr>
          <td>Total</td><td>{{ total['KEYWORD'] }}</td><td>{{ total['ID'] }}</td><td>{{ total['NUM'] }}</td><td>{{ total['SYM'] }}</td><td>{{ total['ERR'] }}</td>
        </tr>
      </table>
    </div>
    {% endif %}
    {% if syntactic or semantic %}
    <div>
      <h2>Analizador Sintáctico y Semántico</h2>
      <table>
        <tr>
          <th>Sintáctico</th><th>Semántico</th>
        </tr>
        <tr>
          <td>{{ syntactic }}</td><td>{{ semantic }}</td>
        </tr>
      </table>
    </div>
    {% endif %}
  </div>
</body>
</html>
'''

def analyze_lexical(code):
    lexer = lex.lex()
    lexer.input(code)
    results = {'KEYWORD': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'STRING': 0, 'ERR': 0}
    rows = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        row = [''] * 6
        if tok.type in results:
            results[tok.type] += 1
            row[list(results.keys()).index(tok.type)] = 'x'
        rows.append(row)
    return rows, results

def analyze_syntactic(code):
    errors = []

    # Verificar la estructura básica de un programa Go
    if "package main" not in code:
        errors.append("El código debe contener 'package main'.")
    if "func main()" not in code:
        errors.append("El código debe contener 'func main()'.")

    # Verificar la estructura de bucles y condicionales
    stack = []
    lines = code.split('\n')
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.endswith('{'):
            stack.append('{')
        elif stripped_line.endswith('}'):
            if not stack:
                errors.append(f"Llave de cierre sin apertura correspondiente en la línea {i + 1}.")
            else:
                stack.pop()

    if stack:
        errors.append("Una o más llaves de apertura no tienen cierre correspondiente.")

    # Verificar la estructura del bucle for
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith("for"):
            if not re.match(r'for\s+(int|string)\s+\w+\s*=\s*(\d+|".*?");\s*\w+\s*<\s*\d+;\s*\w+\+\+', stripped_line):
                errors.append(f"Estructura de bucle 'for' incorrecta en la línea {i + 1}: {line}")

    if not errors:
        return "Sintaxis correcta"
    else:
        return " ".join(errors)

def analyze_semantic(code):
    errors = []

    # Verificar el uso correcto de Println
    if "fmt.Println" not in code:
        errors.append("El código debe usar 'fmt.Println' para imprimir.")

    # Verificar consistencia de variables en bucles y condiciones
    variable_pattern = re.compile(r'for\s+(int|string)\s+(\w+)\s*=\s*(\d+|".*?");\s*\2\s*<\s*\d+;\s*\2\+\+')
    lines = code.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("for"):
            match = variable_pattern.search(line)
            if not match:
                errors.append(f"Estructura de bucle 'for' incorrecta en la línea: {line}")

    if not errors:
        return "Uso correcto de las estructuras semánticas"
    else:
        return " ".join(errors)

@app.route('/', methods=['GET', 'POST'])
def index():
    code = ''
    lexical_results = []
    total_results = {'KEYWORD': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'STRING': 0, 'ERR': 0}
    syntactic_result = ''
    semantic_result = ''
    if request.method == 'POST':
        code = request.form['code']
        lexical_results, total_results = analyze_lexical(code)
        syntactic_result = analyze_syntactic(code)
        semantic_result = analyze_semantic(code)
    return render_template_string(html_template, code=code, lexical=lexical_results, total=total_results, syntactic=syntactic_result, semantic=semantic_result)

if __name__ == '__main__':
    app.run(debug=True)
