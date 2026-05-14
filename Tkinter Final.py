from tkinter import *
import requests
import threading
import time
import random
import json
import os

#Config global
PICO_IP  = None
INTERVALO = 0.4

unidad_actual = 0.2
def Get_unidad():
    return unidad_actual

# Velocidades para Modo Transmision Simple (3 niveles)
VELOCIDADES = [0.3, 0.2, 0.1]   # lento → medio → rapido
PUNTAJES_NIVEL = [1, 2, 3]       # puntos por caracter correcto segun nivel

# Top 10 persistente en archivo local
TOP10_FILE = "top10.json"

#Carga .jason con top 10 puntajes
def Cargar_top10():
    if os.path.exists(TOP10_FILE):
        with open(TOP10_FILE, "r") as f:
            return json.load(f)
    return []

#Guarda los puntajes en .json
def Guardar_top10(top10):
    with open(TOP10_FILE, "w") as f:
        json.dump(top10, f)

#Agrega nombres a top 10
def Insertar_top10(nombre, puntaje):
    top10 = Cargar_top10()
    top10.append({"nombre": nombre, "puntaje": puntaje})
    top10 = sorted(top10, key=lambda x: x["puntaje"], reverse=True)[:10]
    Guardar_top10(top10)
    posicion = next((i+1 for i, e in enumerate(top10) if e["nombre"] == nombre and e["puntaje"] == puntaje), None)
    return top10, posicion

#Palabras del juego
PALABRAS = ["SI", "SOS", "NO", "NOSE", "HOLA", "ADIOS", "LUIS", "CE1104", "CLAUDE", "67"]

#Diccionario morse
MORSE_A_TEXTO = {
    ".-": "A",    "-...": "B",  "-.-.": "C",  "-..": "D",
    ".": "E",     "..-.": "F",  "--.": "G",   "....": "H",
    "..": "I",    ".---": "J",  "-.-": "K",   ".-..": "L",
    "--": "M",    "-.": "N",    "---": "O",   ".--.": "P",
    "--.-": "Q",  ".-.": "R",   "...": "S",   "-": "T",
    "..-": "U",   "...-": "V",  ".--": "W",   "-..-": "X",
    "-.--": "Y",  "--..": "Z",
    ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9", "-----": "0",
    ".-.-.": "+", "-....-": "-",
}

#Inverso
TEXTO_A_MORSE = {v: k for k, v in MORSE_A_TEXTO.items()}

def Decodificar_simbolo(simbolo):
    return MORSE_A_TEXTO.get(simbolo, '')

def Decodificar_cadena(morse):
    resultado = ''
    for simbolo in morse.split():
        resultado += Decodificar_simbolo(simbolo)
    return resultado


#HTTP----------------------------------------------------


#Hace un GET a la pico, sacando el morse acumulado, retorna texto 
def Enviar_comando(ruta):
    if PICO_IP is None:
        return None
    try:
        r = requests.get(f'{PICO_IP}/{ruta}', timeout=4)
        return r.text.strip()
    except Exception as e:
        print(f'Error de conexion: {e}')
        return None

#se conecta a la pico con el IP ingresado
def Conectar(Ent_ip, Lbl_conexion):
    global PICO_IP
    ip = Ent_ip.get().strip()
    if not ip:
        Lbl_conexion.config(text='Ingresa una IP', fg=COLOR_ACENTO)
        return
    PICO_IP = f'http://{ip}'
    respuesta = Enviar_comando('')
    if respuesta is not None:
        Lbl_conexion.config(text=f'✔  Conectado a {ip}', fg=COLOR_VERDE)
    else:
        Lbl_conexion.config(text='✘  No se pudo conectar', fg=COLOR_ACENTO)
        PICO_IP = None

#Para ocultar pantallas actuales
def CambiarPantalla(nueva):
    global pantalla_actual
    pantalla_actual.pack_forget()
    nueva.pack(fill=BOTH, expand=True)
    pantalla_actual = nueva

#Colores y estilos
BG             = "#c872cf"
COLOR_PANEL    = "#1a1a2e"
COLOR_ACENTO   = "#f3a033"
COLOR_ACENTO2  = "#da922f"
COLOR_TEXTO    = "#eaeaea"
COLOR_GRIS     = "#FFFFFF"
COLOR_VERDE    = "#2ecc71"
COLOR_AMARILLO = "#f1c40f"
COLOR_ROJO     = "#e94560"

FUENTE       = 'Lexend'
FONT_TITLE   = (FUENTE, 22, "bold")
FONT_GRANDE  = (FUENTE, 16, "bold")
FONT_MEDIANA = (FUENTE, 12)
FONT_PEQUENA = (FUENTE, 10)

nombre_j1 = ''
nombre_j2 = ''
modo_juego = ''  # 'simple' o 'escucha'

#Variables teclado
tec_presionado  = False
tec_t_inicio    = 0.0
tec_simbolos    = []
tec_texto       = []
tec_timer_char  = None
tec_timer_palabra = None

#Variables de respuestas
respuesta_boton   = ''
respuesta_teclado = ''
palabra_actual    = ''

#Labels globales para funciones
Lbl_morse_raw     = None
Lbl_boton_texto   = None
Lbl_simbolos      = None
Lbl_char_actual   = None
Lbl_teclado_texto = None
Lbl_estado_tec    = None
Lbl_nombre1       = None
Lbl_nombre2       = None
Lbl_obj_palabra   = None

# Main -----------------------------------
VENTANA = Tk()
VENTANA.title('STRANGER TEC')
VENTANA.configure(bg=BG)
VENTANA.resizable(False, False)

# ─────────────────────────────────────────
# Ventana de referencia de morse
# ─────────────────────────────────────────

def Abrir_referencia_morse():
    if hasattr(Abrir_referencia_morse, 'ventana') and Abrir_referencia_morse.ventana.winfo_exists():
        Abrir_referencia_morse.ventana.lift()
        return
    ref = Toplevel(VENTANA)
    ref.title('Referencia Morse')
    ref.configure(bg=BG)
    ref.resizable(False, False)
    Abrir_referencia_morse.ventana = ref

    Label(ref, text='CODIGO MORSE', font=FONT_GRANDE, fg=COLOR_ACENTO, bg=BG).pack(pady=(16, 4))
    Label(ref, text='=' * 44, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=2)

    Frm_ref_cuerpo = Frame(ref, bg=BG)
    Frm_ref_cuerpo.pack(padx=20, pady=8)
    Frm_letras = Frame(Frm_ref_cuerpo, bg=BG)
    Frm_nums   = Frame(Frm_ref_cuerpo, bg=BG)
    Frm_letras.grid(row=0, column=0, padx=16, sticky='n')
    Frm_nums.grid(row=0,   column=1, padx=16, sticky='n')

    Label(Frm_letras, text='LETRA', width=6,  font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=0)
    Label(Frm_letras, text='MORSE', width=10, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=1)
    Label(Frm_nums,   text='CHAR',  width=6,  font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=0)
    Label(Frm_nums,   text='MORSE', width=10, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=1)

    fila_letras = fila_nums = 1
    for simbolo, char in MORSE_A_TEXTO.items():
        if char.isalpha() and fila_letras < 20:
            Label(Frm_letras, text=char,    width=6,  font=FONT_MEDIANA, fg=COLOR_TEXTO,    bg=BG).grid(row=fila_letras, column=0, pady=1)
            Label(Frm_letras, text=simbolo, width=10, font=FONT_MEDIANA, fg=COLOR_AMARILLO, bg=BG).grid(row=fila_letras, column=1, pady=1)
            fila_letras += 1
        else:
            Label(Frm_nums, text=char,    width=6,  font=FONT_MEDIANA, fg=COLOR_TEXTO,    bg=BG).grid(row=fila_nums, column=0, pady=1)
            Label(Frm_nums, text=simbolo, width=10, font=FONT_MEDIANA, fg=COLOR_AMARILLO, bg=BG).grid(row=fila_nums, column=1, pady=1)
            fila_nums += 1

    Label(ref, text='=' * 44, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=(4, 16))

# ─────────────────────────────────────────
# Morse de tecla espacio
# ─────────────────────────────────────────

#Actualiza labels en pantalla con estado actual del morse y acumula texto 
def Actualizar_display_teclado():
    global respuesta_teclado
    secuencia = ''.join(tec_simbolos)
    Lbl_simbolos.config(text=secuencia if secuencia else "·")
    Lbl_char_actual.config(text=Decodificar_simbolo(secuencia) if secuencia else "")
    texto_actual = ''.join(tec_texto)
    Lbl_teclado_texto.config(text=texto_actual)
    respuesta_teclado = texto_actual


#Se llama despues de pausa de 3 unidades sin presionar, toma simbolos acumulados y los hace en letra para ponerlos al texto acumulado
def Confirmar_caracter():
    global tec_timer_char
    if tec_timer_char is not None:
        VENTANA.after_cancel(tec_timer_char)
        tec_timer_char = None
    secuencia = ''.join(tec_simbolos)
    if secuencia:
        char = Decodificar_simbolo(secuencia)
        tec_texto.append(char)
        tec_simbolos.clear()
        Lbl_estado_tec.config(text=f'{secuencia} → {char}', fg=COLOR_VERDE)
    Actualizar_display_teclado()

#Para medir cuando se presiona el espacio, empieza a timear
def Espacio_presionado(evento):
    global tec_presionado, tec_t_inicio, tec_timer_char, tec_timer_palabra
    if tec_presionado:
        return
    if tec_timer_char is not None:
        VENTANA.after_cancel(tec_timer_char)
        tec_timer_char = None
    if tec_timer_palabra is not None:
        VENTANA.after_cancel(tec_timer_palabra)
        tec_timer_palabra = None
    tec_presionado = True
    tec_t_inicio = time.time()
    Lbl_estado_tec.config(text='● Presionando...', fg=COLOR_ACENTO)


#Cuando se suelta el espacio, calcula tiempos para determinar si fue linea o raya
def Espacio_al_soltar(evento):
    global tec_presionado, tec_timer_char, tec_timer_palabra
    if not tec_presionado:
        return
    duracion = time.time() - tec_t_inicio
    tec_presionado = False
    unidad = Get_unidad()
    simbolo = '.' if duracion < unidad * 2 else '-'
    tec_simbolos.append(simbolo)
    Actualizar_display_teclado()
    Lbl_estado_tec.config(text=f'{"Punto" if simbolo=="." else "Raya"} ({duracion:.2f}s)', fg=COLOR_GRIS)
    tec_timer_char    = VENTANA.after(int(unidad * 3 * 1000), Confirmar_caracter)

#Activa eventos de teclado
def Bind_teclado():
    VENTANA.bind("<KeyPress-space>",   Espacio_presionado)
    VENTANA.bind("<KeyRelease-space>", Espacio_al_soltar)

#Desactiva eventos de teclado
def Unbind_teclado():
    VENTANA.unbind("<KeyPress-space>")
    VENTANA.unbind("<KeyRelease-space>")

#resetea las variables para cada turno
def Limpiar_teclado():
    global tec_presionado, tec_t_inicio, tec_timer_char, tec_timer_palabra
    tec_presionado = False
    tec_t_inicio   = 0.0
    tec_simbolos.clear()
    tec_texto.clear()
    tec_timer_char    = None
    tec_timer_palabra = None

# ─────────────────────────────────────────
# Lectura del boton de la pico
# ─────────────────────────────────────────

#actualiza label del boton
def Actualizar_label_boton():
    Lbl_boton_texto.config(text=respuesta_boton)

#Corre hilo en segundo plano, detectando cada 0.4 segundos si hay morse nuevo con GET_MORSE(), si hay, lo decodifica y lo pone al texto del boton
def Loop_polling():
    global respuesta_boton
    while True:
        time.sleep(INTERVALO)
        if PICO_IP is None:
            continue
        morse = Enviar_comando('GET_MORSE')
        if morse:
            respuesta_boton += Decodificar_cadena(morse)
            Lbl_boton_texto.after(0, Actualizar_label_boton)

#Limpia texto acumulado del boton
def Limpiar_boton():
    global respuesta_boton
    respuesta_boton = ''
    if Lbl_boton_texto:
        Lbl_boton_texto.config(text='')

# ─────────────────────────────────────────
# Puntajes
# ─────────────────────────────────────────

#Compara letra por letra, por cada letra buena, suma 1 punto al multiplicador
def Calcular_puntos(objetivo, respuesta, multiplicador=1):
    puntos = 0
    for i, char in enumerate(objetivo):
        if i < len(respuesta) and respuesta[i] == char:
            puntos += multiplicador
    return puntos

#Muestra una fila de comparacion letra por letra en la pantalla de resultados, las letras buenas en verde, las malas en rojo
def Mostrar_comparacion(padre, etiqueta, texto, objetivo, color_label):
    Frm_fila = Frame(padre, bg=BG)
    Frm_fila.pack(anchor='w', pady=1)
    Label(Frm_fila, text=f'{etiqueta:<14}', font=(FUENTE, 11), fg=color_label, bg=BG).pack(side=LEFT)
    if not texto:
        Label(Frm_fila, text='(vacio)', font=(FUENTE, 11), fg=COLOR_GRIS, bg=BG).pack(side=LEFT)
        return
    for i, char in enumerate(texto):
        if char == " ":
            Label(Frm_fila, text=" ", font=(FUENTE, 14, "bold"), bg=BG).pack(side=LEFT)
            continue
        color = COLOR_VERDE if (i < len(objetivo) and objetivo[i] == char) else COLOR_ROJO
        Label(Frm_fila, text=char, font=(FUENTE, 14, "bold"), fg=color, bg=BG).pack(side=LEFT)

# ══════════════════════════════════════════════════════════════
# PANTALLA CONFIG
# ══════════════════════════════════════════════════════════════
Contenedor_Pantalla_Config = Frame(VENTANA, bg=BG)
Contenedor_Pantalla_Config.pack(fill=BOTH, expand=True)
pantalla_actual = Contenedor_Pantalla_Config

Label(Contenedor_Pantalla_Config, text='STRANGER TEC',        font=FONT_TITLE,   fg=COLOR_ACENTO, bg=BG).pack(pady=(24,4))
Label(Contenedor_Pantalla_Config, text='Configuracion Inicial', font=FONT_PEQUENA, fg=COLOR_GRIS,   bg=BG).pack()
Label(Contenedor_Pantalla_Config, text='=' * 60,              font=FONT_PEQUENA, fg=COLOR_GRIS,   bg=BG).pack(pady=4)
Label(Contenedor_Pantalla_Config, text='JUGADORES',           font=FONT_GRANDE,  fg=COLOR_TEXTO,  bg=BG).pack()

Frm_jugadores = Frame(Contenedor_Pantalla_Config, bg=BG)
Frm_jugadores.pack(pady=8)
Label(Frm_jugadores, text='Jugador 1:', fg=COLOR_ACENTO, bg=BG, font=FONT_MEDIANA).grid(row=0, column=0, sticky='e', padx=6, pady=8)
Ent_jugador1 = Entry(Frm_jugadores, width=18, bg=COLOR_PANEL, fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO, font=FONT_MEDIANA, relief=FLAT, bd=4)
Ent_jugador1.grid(row=0, column=1, padx=6)
Label(Frm_jugadores, text='Jugador 2:', fg=COLOR_ACENTO, bg=BG, font=FONT_MEDIANA).grid(row=1, column=0, sticky='e', padx=6, pady=8)
Ent_jugador2 = Entry(Frm_jugadores, width=18, bg=COLOR_PANEL, fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO, font=FONT_MEDIANA, relief=FLAT, bd=4)
Ent_jugador2.grid(row=1, column=1, padx=6)

#COnecxion a pico W
Label(Contenedor_Pantalla_Config, text='=' * 60,          font=FONT_PEQUENA, fg=COLOR_GRIS,  bg=BG).pack(pady=4)
Label(Contenedor_Pantalla_Config, text='CONEXION PICO W', font=FONT_GRANDE,  fg=COLOR_TEXTO, bg=BG).pack()

Frm_ip = Frame(Contenedor_Pantalla_Config, bg=BG)
Frm_ip.pack(pady=6)
Label(Frm_ip, text="IP:", fg=COLOR_TEXTO, font=FONT_MEDIANA, bg=BG).pack(side=LEFT)
Ent_ip = Entry(Frm_ip, width=16, bg=COLOR_PANEL, fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO, relief=FLAT, bd=4, font=FONT_MEDIANA)
Ent_ip.pack(side=LEFT, padx=10)
Ent_ip.insert(0, "10.133.245.98")

Lbl_conexion = Label(Contenedor_Pantalla_Config, text='Sin conectar', fg=COLOR_GRIS, bg=BG, font=FONT_PEQUENA)
Lbl_conexion.pack()

def FUNC_Btn_conectar():
    Conectar(Ent_ip, Lbl_conexion)

Button(Contenedor_Pantalla_Config, text='Conectar', bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
       relief=FLAT, padx=12, pady=4, command=FUNC_Btn_conectar, font=FONT_MEDIANA).pack(pady=4)

Label(Contenedor_Pantalla_Config, text='=' * 60,     font=FONT_PEQUENA, fg=COLOR_GRIS,  bg=BG).pack(pady=4)
Label(Contenedor_Pantalla_Config, text='MODO DE JUEGO', font=FONT_GRANDE, fg=COLOR_TEXTO, bg=BG).pack()

Frm_modos = Frame(Contenedor_Pantalla_Config, bg=BG)
Frm_modos.pack(pady=10)

Lbl_error_cfg = Label(Contenedor_Pantalla_Config, text='', fg=COLOR_ROJO, bg=BG, font=FONT_PEQUENA)
Lbl_error_cfg.pack()

#Revisa que esten nombres ingresados
def Validar_e_iniciar(modo):
    global nombre_j1, nombre_j2, modo_juego
    nombre_j1 = Ent_jugador1.get().strip()
    nombre_j2 = Ent_jugador2.get().strip()
    if not nombre_j1:
        Lbl_error_cfg.config(text="Ingresa el nombre del Jugador 1")
        return
    if not nombre_j2 and modo == 'escucha':
        Lbl_error_cfg.config(text="Ingresa el nombre del Jugador 2")
        return
    if not nombre_j2:
        nombre_j2 = 'CPU'
    modo_juego = modo
    Lbl_error_cfg.config(text='')
    if modo == 'simple':
        Iniciar_modo_simple()
    else:
        Iniciar_modo_escucha()

Button(Frm_modos, text='⚡  TRANSMISION SIMPLE',
       bg=COLOR_ACENTO, fg='white', font=FONT_GRANDE, relief=FLAT, padx=16, pady=10,
       command=lambda: Validar_e_iniciar('simple')).grid(row=0, column=0, padx=10, pady=6)

Button(Frm_modos, text='👂  ESCUCHA Y TRANSMISION',
       bg=COLOR_ACENTO2, fg='white', font=FONT_GRANDE, relief=FLAT, padx=16, pady=10,
       command=lambda: Validar_e_iniciar('escucha')).grid(row=0, column=1, padx=10, pady=6)

# ══════════════════════════════════════════════════════════════
#Modo trasmision simple
# ══════════════════════════════════════════════════════════════
nivel_actual   = 0   # 0,1,2 (3 niveles)
puntaje_simple = 0
frases_simple  = []

Contenedor_Simple = Frame(VENTANA, bg=BG)

# Widgets del modo simple
Lbl_simple_nivel   = None
Lbl_simple_frase   = None
Lbl_simple_estado  = None
Lbl_simple_puntaje = None
Lbl_simple_simb    = None
Lbl_simple_char    = None
Lbl_simple_texto   = None
Lbl_simple_estec   = None

#Inicia y muestra el modo transmision simple, crea widget y elige 3 frases aleatorias
def Iniciar_modo_simple():
    global nivel_actual, puntaje_simple, frases_simple, unidad_actual
    global Lbl_simple_nivel, Lbl_simple_frase, Lbl_simple_estado
    global Lbl_simple_puntaje, Lbl_simple_simb, Lbl_simple_char
    global Lbl_simple_texto, Lbl_simple_estec
    global Lbl_simbolos, Lbl_char_actual, Lbl_teclado_texto, Lbl_estado_tec

    nivel_actual   = 0
    puntaje_simple = 0
    frases_simple  = random.sample(PALABRAS, min(3, len(PALABRAS))) 
    unidad_actual  = VELOCIDADES[0]

    # Limpia widgets por si se reincia
    for w in Contenedor_Simple.winfo_children():
        w.destroy()

    # Header y puntaje 
    Frm_h = Frame(Contenedor_Simple, bg=COLOR_PANEL)
    Frm_h.pack(fill=X)
    Label(Frm_h, text='TRANSMISION SIMPLE', font=FONT_TITLE, fg=COLOR_ACENTO, bg=COLOR_PANEL).pack(side=LEFT, padx=16, pady=10)
    Lbl_simple_puntaje = Label(Frm_h, text='Puntaje: 0', font=FONT_GRANDE, fg=COLOR_AMARILLO, bg=COLOR_PANEL)
    Lbl_simple_puntaje.pack(side=RIGHT, padx=16)

    Label(Contenedor_Simple, text=f'Jugador: {nombre_j1}', font=FONT_MEDIANA, fg=COLOR_TEXTO, bg=BG).pack(pady=(12,2))

    Lbl_simple_nivel = Label(Contenedor_Simple, text='NIVEL 1 — Velocidad lenta', font=FONT_GRANDE, fg=COLOR_AMARILLO, bg=BG)
    Lbl_simple_nivel.pack(pady=4)

    Label(Contenedor_Simple, text='La maqueta transmitirá la frase. Descifrala:', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack()
    Lbl_simple_frase = Label(Contenedor_Simple, text='???', font=(FUENTE, 32, "bold"), fg=COLOR_ACENTO, bg=BG)
    Lbl_simple_frase.pack(pady=8)

    Lbl_simple_estado = Label(Contenedor_Simple, text='Enviando a la maqueta...', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG)
    Lbl_simple_estado.pack()

    Label(Contenedor_Simple, text='=' * 60, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=6)
    Label(Contenedor_Simple, text='Tu respuesta (barra espaciadora):', font=FONT_MEDIANA, fg=COLOR_TEXTO, bg=BG).pack()

    Frm_tec = Frame(Contenedor_Simple, bg=COLOR_PANEL)
    Frm_tec.pack(padx=20, pady=6, fill=X)

    Lbl_simple_simb = Label(Frm_tec, text='·', font=(FUENTE, 14), fg=COLOR_ACENTO2, bg=COLOR_PANEL)
    Lbl_simple_simb.pack()
    Lbl_simple_char = Label(Frm_tec, text='', font=(FUENTE, 22, "bold"), fg=COLOR_AMARILLO, bg=COLOR_PANEL)
    Lbl_simple_char.pack()
    Lbl_simple_texto = Label(Frm_tec, text='', font=(FUENTE, 20, "bold"), fg=COLOR_TEXTO, bg=COLOR_PANEL, wraplength=400)
    Lbl_simple_texto.pack(pady=4)
    Lbl_simple_estec = Label(Frm_tec, text='Presiona espacio', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL)
    Lbl_simple_estec.pack(pady=(0, 8))

    # Redirigir los labels globales del teclado a esta pantalla para que las funciones del teclado actualizen los labels bien
    Lbl_simbolos      = Lbl_simple_simb
    Lbl_char_actual   = Lbl_simple_char
    Lbl_teclado_texto = Lbl_simple_texto
    Lbl_estado_tec    = Lbl_simple_estec

    Label(Contenedor_Simple, text='=' * 60, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Frm_btn = Frame(Contenedor_Simple, bg=BG)
    Frm_btn.pack(pady=8)
    Button(Frm_btn, text='✔  CONFIRMAR RESPUESTA', bg=COLOR_VERDE, fg='#0f0f1a',
           font=FONT_GRANDE, relief=FLAT, padx=16, pady=8,
           command=Confirmar_nivel_simple).pack(side=LEFT, padx=8)
    Button(Frm_btn, text='REFERENCIA MORSE', bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
           font=FONT_GRANDE, relief=FLAT, padx=16, pady=8,
           command=Abrir_referencia_morse).pack(side=LEFT, padx=8)

    CambiarPantalla(Contenedor_Simple)
    Limpiar_teclado()
    Bind_teclado()
    Arrancar_nivel_simple()

#Empieza el nivel, ajusta velocidades, y envia la frase a la maqueta por hilo separado para no congelar la interfaz mientras espera la respuesta del servidor
def Arrancar_nivel_simple():
    global unidad_actual
    unidad_actual = VELOCIDADES[nivel_actual]
    frase = frases_simple[nivel_actual]
    nombres_nivel = ['NIVEL 1 — Velocidad lenta', 'NIVEL 2 — Velocidad media', 'NIVEL 3 — Velocidad rapida']
    Lbl_simple_nivel.config(text=nombres_nivel[nivel_actual])
    Lbl_simple_frase.config(text='???')
    Lbl_simple_estado.config(text='Enviando a la maqueta...', fg=COLOR_GRIS)
    Limpiar_teclado()

    def enviar_y_esperar():
        Enviar_comando(f'FRASE_{frase}')
        Lbl_simple_estado.after(0, lambda: Lbl_simple_estado.config(
            text=f'Maqueta transmitiendo... descifra lo que ves/escuchas', fg=COLOR_VERDE))

    threading.Thread(target=enviar_y_esperar, daemon=True).start()

#Cuando el jugador apreta CONFIRMAR RESPUESTA y pasa al siguiente nivel o termina el juego
def Confirmar_nivel_simple():
    global nivel_actual, puntaje_simple
    Confirmar_caracter()
    objetivo  = frases_simple[nivel_actual]
    respuesta = respuesta_teclado.replace(' ', '').upper()
    puntos    = Calcular_puntos(objetivo, respuesta, PUNTAJES_NIVEL[nivel_actual])
    puntaje_simple += puntos
    Lbl_simple_puntaje.config(text=f'Puntaje: {puntaje_simple}')

    nivel_actual += 1
    Unbind_teclado()

    if nivel_actual < 3:
        # Mostrar resultado breve y pasar al siguiente nivel
        Lbl_simple_estado.config(
            text=f'Nivel completado! +{puntos} pts  |  Objetivo era: {objetivo}  |  Tu respuesta: {respuesta}',
            fg=COLOR_AMARILLO)
        VENTANA.after(3000, lambda: [Limpiar_teclado(), Bind_teclado(), Arrancar_nivel_simple()])
    else:
        # Fin de los 3 niveles → pantalla de resultados simple
        VENTANA.after(500, lambda: Mostrar_resultado_simple(objetivo, respuesta))

#muestra puntajes y los registra en el top 10
def Mostrar_resultado_simple(ultimo_obj, ultima_resp):
    global puntaje_simple
    top10, posicion = Insertar_top10(nombre_j1, puntaje_simple)

    for w in Contenedor_Pantalla_Puntaje.winfo_children():
        w.destroy()

    Label(Contenedor_Pantalla_Puntaje, text='RESULTADO FINAL', font=FONT_TITLE, fg=COLOR_ACENTO, bg=BG).pack(pady=(24,4))
    Label(Contenedor_Pantalla_Puntaje, text=f'Jugador: {nombre_j1}', font=FONT_GRANDE, fg=COLOR_TEXTO, bg=BG).pack()
    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Label(Contenedor_Pantalla_Puntaje, text=f'PUNTAJE TOTAL: {puntaje_simple}',
          font=(FUENTE, 28, "bold"), fg=COLOR_AMARILLO, bg=BG).pack(pady=8)

    if posicion:
        Label(Contenedor_Pantalla_Puntaje,
              text=f'🏆  Entraste al Top 10 en el puesto #{posicion}!',
              font=FONT_GRANDE, fg=COLOR_VERDE, bg=BG).pack(pady=4)
    else:
        Label(Contenedor_Pantalla_Puntaje, text='No entraste al Top 10 esta vez.',
              font=FONT_MEDIANA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)
    Label(Contenedor_Pantalla_Puntaje, text='TOP 10', font=FONT_GRANDE, fg=COLOR_ACENTO, bg=BG).pack()

    Frm_top = Frame(Contenedor_Pantalla_Puntaje, bg=BG)
    Frm_top.pack(pady=6)
    for i, entry in enumerate(top10):
        color = COLOR_AMARILLO if i == 0 else COLOR_TEXTO
        Label(Frm_top, text=f'#{i+1}  {entry["nombre"]:<16} {entry["puntaje"]} pts',
              font=FONT_MEDIANA, fg=color, bg=BG).pack(anchor='w')

    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Frm_btn = Frame(Contenedor_Pantalla_Puntaje, bg=BG)
    Frm_btn.pack(pady=(4, 24))
    Button(Frm_btn, text='JUGAR DE NUEVO', bg=COLOR_ACENTO, fg='white',
           font=FONT_MEDIANA, relief=FLAT, padx=12, pady=6,
           command=Iniciar_modo_simple).pack(side=LEFT, padx=8)
    Button(Frm_btn, text='MENU PRINCIPAL', bg=COLOR_PANEL, fg=COLOR_TEXTO,
           font=FONT_MEDIANA, relief=FLAT, padx=12, pady=6,
           command=lambda: CambiarPantalla(Contenedor_Pantalla_Config)).pack(side=LEFT, padx=8)

    CambiarPantalla(Contenedor_Pantalla_Puntaje)


# ══════════════════════════════════════════════════════════════
# MODO ESCUCHA Y TRANSMISION
# ══════════════════════════════════════════════════════════════
turno_escucha   = 1   # 1 = turno inicial, 2 = turno invertido
puntaje_j1_esc  = 0
puntaje_j2_esc  = 0
# En turno 1: J1=teclado J2=boton | Turno 2: J1=boton J2=teclado
frase_escucha   = ''

Contenedor_Escucha = Frame(VENTANA, bg=BG)

Lbl_esc_turno   = None
Lbl_esc_frase   = None
Lbl_esc_estado  = None
Lbl_esc_pts1    = None
Lbl_esc_pts2    = None
Lbl_esc_simb    = None
Lbl_esc_char    = None
Lbl_esc_texto   = None
Lbl_esc_estec   = None
Lbl_esc_boton   = None
Lbl_esc_nb1     = None
Lbl_esc_nb2     = None

def Iniciar_modo_escucha():
    global turno_escucha, puntaje_j1_esc, puntaje_j2_esc, frase_escucha
    global Lbl_esc_turno, Lbl_esc_frase, Lbl_esc_estado
    global Lbl_esc_pts1, Lbl_esc_pts2
    global Lbl_esc_simb, Lbl_esc_char, Lbl_esc_texto, Lbl_esc_estec, Lbl_esc_boton
    global Lbl_esc_nb1, Lbl_esc_nb2
    global Lbl_simbolos, Lbl_char_actual, Lbl_teclado_texto, Lbl_estado_tec
    global Lbl_boton_texto, Lbl_nombre1, Lbl_nombre2

    turno_escucha  = 1
    puntaje_j1_esc = 0
    puntaje_j2_esc = 0
    frase_escucha  = random.choice(PALABRAS)

    for w in Contenedor_Escucha.winfo_children():
        w.destroy()

    # Header
    Frm_h = Frame(Contenedor_Escucha, bg=COLOR_PANEL)
    Frm_h.pack(fill=X)
    Label(Frm_h, text='ESCUCHA Y TRANSMISION', font=FONT_TITLE, fg=COLOR_ACENTO, bg=COLOR_PANEL).pack(side=LEFT, padx=16, pady=10)

    Frm_pts = Frame(Frm_h, bg=COLOR_PANEL)
    Frm_pts.pack(side=RIGHT, padx=16)
    Lbl_esc_pts1 = Label(Frm_pts, text=f'{nombre_j1}: 0 pts', font=FONT_MEDIANA, fg=COLOR_ACENTO,   bg=COLOR_PANEL)
    Lbl_esc_pts1.pack(anchor='e')
    Lbl_esc_pts2 = Label(Frm_pts, text=f'{nombre_j2}: 0 pts', font=FONT_MEDIANA, fg=COLOR_AMARILLO, bg=COLOR_PANEL)
    Lbl_esc_pts2.pack(anchor='e')

    Lbl_esc_turno = Label(Contenedor_Escucha, text='TURNO 1', font=FONT_GRANDE, fg=COLOR_AMARILLO, bg=BG)
    Lbl_esc_turno.pack(pady=(12,2))

    Label(Contenedor_Escucha, text='Frase a descifrar (la maqueta transmitirá):', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack()
    Lbl_esc_frase = Label(Contenedor_Escucha, text=frase_escucha, font=(FUENTE, 32, "bold"), fg=COLOR_ACENTO, bg=BG)
    Lbl_esc_frase.pack(pady=4)

    Lbl_esc_estado = Label(Contenedor_Escucha, text='Enviando a la maqueta...', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG)
    Lbl_esc_estado.pack()

    Label(Contenedor_Escucha, text='=' * 60, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    # Area de 2 columnas
    Frm_arena = Frame(Contenedor_Escucha, bg=BG)
    Frm_arena.pack(fill=BOTH, expand=True, padx=10)
    Frm_arena.columnconfigure(0, weight=1)
    Frm_arena.columnconfigure(1, weight=1)

    Frm_col1 = Frame(Frm_arena, bg=COLOR_PANEL)
    Frm_col2 = Frame(Frm_arena, bg=COLOR_PANEL)
    Frm_col1.grid(row=0, column=0, padx=8, pady=4, sticky="nsew")
    Frm_col2.grid(row=0, column=1, padx=8, pady=4, sticky="nsew")

    # Col1 = J1 (teclado en turno 1, boton en turno 2)
    Lbl_esc_nb1 = Label(Frm_col1, text=nombre_j1, font=FONT_GRANDE, fg=COLOR_ACENTO, bg=COLOR_PANEL)
    Lbl_esc_nb1.pack(pady=(12,2))
    Label(Frm_col1, text='[BARRA ESPACIADORA]', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack()
    Label(Frm_col1, text='Simbolo:', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack(pady=(6,0))
    Lbl_esc_simb = Label(Frm_col1, text='·', font=(FUENTE, 14), fg=COLOR_ACENTO2, bg=COLOR_PANEL)
    Lbl_esc_simb.pack()
    Label(Frm_col1, text='Caracter:', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack()
    Lbl_esc_char = Label(Frm_col1, text='', font=(FUENTE, 20, "bold"), fg=COLOR_AMARILLO, bg=COLOR_PANEL)
    Lbl_esc_char.pack()
    Label(Frm_col1, text='Texto:', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack()
    Lbl_esc_texto = Label(Frm_col1, text='', font=(FUENTE, 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_PANEL, wraplength=180)
    Lbl_esc_texto.pack(pady=(2,2))
    Lbl_esc_estec = Label(Frm_col1, text='Presiona espacio', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL)
    Lbl_esc_estec.pack(pady=(0,12))

    # Col2 = J2 (boton en turno 1, teclado en turno 2)
    Lbl_esc_nb2 = Label(Frm_col2, text=nombre_j2, font=FONT_GRANDE, fg=COLOR_AMARILLO, bg=COLOR_PANEL)
    Lbl_esc_nb2.pack(pady=(12,2))
    Label(Frm_col2, text='[BOTON FISICO]', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack()
    Label(Frm_col2, text='Texto recibido:', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=COLOR_PANEL).pack(pady=(8,0))
    Lbl_esc_boton = Label(Frm_col2, text='', font=(FUENTE, 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_PANEL, wraplength=180)
    Lbl_esc_boton.pack(pady=(2,12))

    # Redirigir labels globales
    Lbl_simbolos      = Lbl_esc_simb
    Lbl_char_actual   = Lbl_esc_char
    Lbl_teclado_texto = Lbl_esc_texto
    Lbl_estado_tec    = Lbl_esc_estec
    Lbl_boton_texto   = Lbl_esc_boton
    Lbl_nombre1       = Lbl_esc_nb1
    Lbl_nombre2       = Lbl_esc_nb2

    Label(Contenedor_Escucha, text='=' * 60, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Frm_btn = Frame(Contenedor_Escucha, bg=BG)
    Frm_btn.pack(pady=(4, 16))
    Button(Frm_btn, text='✔  FIN DE TURNO', bg=COLOR_VERDE, fg='#0f0f1a',
           font=FONT_GRANDE, relief=FLAT, padx=16, pady=8,
           command=Confirmar_turno_escucha).pack(side=LEFT, padx=8)
    Button(Frm_btn, text='REFERENCIA MORSE', bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
           font=FONT_GRANDE, relief=FLAT, padx=16, pady=8,
           command=Abrir_referencia_morse).pack(side=LEFT, padx=8)

    CambiarPantalla(Contenedor_Escucha)
    Limpiar_teclado()
    Limpiar_boton()
    Bind_teclado()
    Arrancar_turno_escucha()

#Empieza el turno 
def Arrancar_turno_escucha():
    Limpiar_teclado()
    Limpiar_boton()
    if turno_escucha == 1:
        Lbl_esc_turno.config(text=f'TURNO 1  —  {nombre_j1}: teclado  |  {nombre_j2}: botón')
    else:
        Lbl_esc_turno.config(text=f'TURNO 2  —  {nombre_j1}: botón  |  {nombre_j2}: teclado')
        # Intercambiar columnas visualmente
        Lbl_esc_nb1.config(text=f'{nombre_j1} [TECLADO]')
        Lbl_esc_nb2.config(text=f'{nombre_j2} [BOTON]')

    Lbl_esc_estado.config(text='Enviando a la maqueta...', fg=COLOR_GRIS)

    def enviar():
        Enviar_comando(f'FRASE_{frase_escucha}')
        Lbl_esc_estado.after(0, lambda: Lbl_esc_estado.config(
            text='Maqueta transmitiendo... ambos jugadores descifren', fg=COLOR_VERDE))

    threading.Thread(target=enviar, daemon=True).start()

#Para finalizar turno, calcula puntaje, acumula puntos, pasa de ronda o termina partida
def Confirmar_turno_escucha():
    global turno_escucha, puntaje_j1_esc, puntaje_j2_esc
    Confirmar_caracter()
    Unbind_teclado()

    objetivo = frase_escucha.upper()

    if turno_escucha == 1:
        # J1 usó teclado, J2 usó botón
        r_j1 = respuesta_teclado.replace(' ', '').upper()
        r_j2 = respuesta_boton.replace(' ', '').upper()
    else:
        # J1 usó botón, J2 usó teclado
        r_j1 = respuesta_boton.replace(' ', '').upper()
        r_j2 = respuesta_teclado.replace(' ', '').upper()

    pts1 = Calcular_puntos(objetivo, r_j1)
    pts2 = Calcular_puntos(objetivo, r_j2)
    puntaje_j1_esc += pts1
    puntaje_j2_esc += pts2

    Lbl_esc_pts1.config(text=f'{nombre_j1}: {puntaje_j1_esc} pts')
    Lbl_esc_pts2.config(text=f'{nombre_j2}: {puntaje_j2_esc} pts')

    if turno_escucha == 1:
        turno_escucha = 2
        Lbl_esc_estado.config(
            text=f'Turno 1 listo! {nombre_j1}:{pts1}pts {nombre_j2}:{pts2}pts — Preparando turno 2...',
            fg=COLOR_AMARILLO)
        VENTANA.after(3000, lambda: [Limpiar_teclado(), Limpiar_boton(), Bind_teclado(), Arrancar_turno_escucha()])
    else:
        VENTANA.after(500, lambda: Mostrar_resultado_escucha())

#Abre ventana para mostrar resultados
def Mostrar_resultado_escucha():
    for w in Contenedor_Pantalla_Puntaje.winfo_children():
        w.destroy()

    Label(Contenedor_Pantalla_Puntaje, text='RESULTADO', font=FONT_TITLE, fg=COLOR_ACENTO, bg=BG).pack(pady=(24,4))
    Label(Contenedor_Pantalla_Puntaje, text=f'Frase: {frase_escucha}', font=FONT_GRANDE, fg=COLOR_TEXTO, bg=BG).pack(pady=4)
    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Frm_tabla = Frame(Contenedor_Pantalla_Puntaje, bg=BG)
    Frm_tabla.pack(pady=8)

    color1 = COLOR_VERDE if puntaje_j1_esc >= puntaje_j2_esc else COLOR_TEXTO
    color2 = COLOR_VERDE if puntaje_j2_esc >= puntaje_j1_esc else COLOR_TEXTO

    Label(Frm_tabla, text='Jugador', width=18, font=FONT_MEDIANA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=0, padx=8)
    Label(Frm_tabla, text='Puntos',  width=10, font=FONT_MEDIANA, fg=COLOR_GRIS, bg=BG).grid(row=0, column=1, padx=8)
    Label(Frm_tabla, text=nombre_j1, width=18, font=FONT_GRANDE,  fg=COLOR_ACENTO,   bg=BG).grid(row=1, column=0, padx=8, pady=4)
    Label(Frm_tabla, text=str(puntaje_j1_esc), width=10, font=FONT_GRANDE, fg=color1, bg=BG).grid(row=1, column=1, padx=8)
    Label(Frm_tabla, text=nombre_j2, width=18, font=FONT_GRANDE,  fg=COLOR_AMARILLO, bg=BG).grid(row=2, column=0, padx=8, pady=4)
    Label(Frm_tabla, text=str(puntaje_j2_esc), width=10, font=FONT_GRANDE, fg=color2, bg=BG).grid(row=2, column=1, padx=8)

    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    if puntaje_j1_esc > puntaje_j2_esc:
        ganador, color_g = nombre_j1, COLOR_ACENTO
    elif puntaje_j2_esc > puntaje_j1_esc:
        ganador, color_g = nombre_j2, COLOR_AMARILLO
    else:
        ganador, color_g = 'EMPATE', COLOR_VERDE

    Label(Contenedor_Pantalla_Puntaje, text='GANADOR', font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack()
    Label(Contenedor_Pantalla_Puntaje, text=f'🏆  {ganador}', font=(FUENTE, 28, "bold"), fg=color_g, bg=BG).pack(pady=4)
    Label(Contenedor_Pantalla_Puntaje, text='=' * 55, font=FONT_PEQUENA, fg=COLOR_GRIS, bg=BG).pack(pady=4)

    Frm_btn = Frame(Contenedor_Pantalla_Puntaje, bg=BG)
    Frm_btn.pack(pady=(4, 24))
    Button(Frm_btn, text='OTRA RONDA',   bg=COLOR_ACENTO2, fg=COLOR_TEXTO,
           font=FONT_MEDIANA, relief=FLAT, padx=12, pady=6,
           command=Iniciar_modo_escucha).pack(side=LEFT, padx=8)
    Button(Frm_btn, text='MENU PRINCIPAL', bg=COLOR_PANEL, fg=COLOR_TEXTO,
           font=FONT_MEDIANA, relief=FLAT, padx=12, pady=6,
           command=lambda: CambiarPantalla(Contenedor_Pantalla_Config)).pack(side=LEFT, padx=8)

    CambiarPantalla(Contenedor_Pantalla_Puntaje)


# ══════════════════════════════════════════════════════════════
#Pantalla de puntos
# ══════════════════════════════════════════════════════════════
Contenedor_Pantalla_Puntaje = Frame(VENTANA, bg=BG)

#Threading en segundo plano
hilo = threading.Thread(target=Loop_polling, daemon=True)
hilo.start()

VENTANA.mainloop()