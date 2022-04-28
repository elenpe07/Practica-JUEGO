"""
Recibe mensajes en: clients/jugando

Publica en: clients/tablero
"""


from paho.mqtt.client import Client
import pygame
import time

oceano=pygame.image.load('oceano.jpg')
oceano=pygame.transform.scale(oceano,(1060,550))
bomba=pygame.image.load('bomba.jpg')
bomba=pygame.transform.scale(bomba,(20,20))




def on_message(mqttc, userdata, msg):    
    mensaje = str(msg.payload)[2:-1]
    pygame.init()
    if mensaje == 'jugador2, se ha ido fuera de rango': 
        data['lanzar'] = True
    elif mensaje == 'jugador1, se ha ido fuera de rango': 
        pass
    elif mensaje == 'HA GANADO EL jugador2':
        print('HAS GANADO')
        ganar = pygame.mixer.Sound("aplausos.mp3")
        pygame.mixer.Sound.play(ganar)
        time.sleep(5)
        pygame.quit()
    elif mensaje == 'HA GANADO EL jugador1':
        print('HAS PERDIDO')
        perder = pygame.mixer.Sound("perder.wav")
        pygame.mixer.Sound.play(perder)
        time.sleep(5)
        pygame.quit()
    elif mensaje == 'jugador2, ya has MARCADO esa casilla antes':
        print('Ya has marcado esa casilla')
        data['lanzar']=True
    elif mensaje == 'jugador1, ya has MARCADO esa casilla antes':
        pass
    elif mensaje == 'Comenzamos' :
        data['lanzar']=True
    elif mensaje == 'jugador1 ha hundido un barco':
        print('Te han hundido un barco')
    elif mensaje == 'jugador2 ha hundido un barco':
        print('Has hundido un barco')
        data['lanzar']=True
    else: #El mensaje recibido son coordenadas de algun tablero
        if len(mensaje.split(','))==3:
            color = (0,0,120) #AZUL
            jugador_y_agua, casilla = mensaje.split(':')
            jugador,agua = jugador_y_agua.split(',')
            fila,columna = casilla.split(',')
            sonido_agua = pygame.mixer.Sound("agua.mp3")
            pygame.mixer.Sound.play(sonido_agua)
            data['lanzar']=True
        else:
            color = (0,255,0) #VERDE
            jugadorYtocado, casillaYhundido  = mensaje.split(':')
            jugador, tocado = jugadorYtocado.split(',')
            fila, columna, hundido = casillaYhundido.split(',')
            data['lanzar']=True
            sonido_bomba = pygame.mixer.Sound("explosion.mp3")
            pygame.mixer.Sound.play(sonido_bomba)
        f = int(fila)
        c = int(columna) 
        if jugador == 'jugador2':
            f = f
            c = c + 22
        tablero[f][c] = color
        pantalla = pygame.display.set_mode([1060, 550]) #dimensión ventana
        pantalla.blit(oceano,(0,0))
        pygame.display.set_caption("TABLERO DEL JUGADOR 2")
        letra = pygame.font.SysFont("PHOSPATE",30)
        texto = letra.render("JUGADOR 2                                                                             JUGADOR 1",True,(0,0,0))
        rectanguloTextoPresent = texto.get_rect()
        rectanguloTextoPresent.centerx = pantalla.get_rect().centerx
        rectanguloTextoPresent.centery = 20
        pantalla.blit(texto,rectanguloTextoPresent)
        for filas in range(20): #dimension tablero a lo alto
            for columnas in range(42): #dimension tablero a lo ancho
                if columnas == 20 or columnas ==21:
                    pass #para que en el margen que separa ambos tableros, se vea el fondo
                else:
                    color_casilla = tablero[filas][columnas]
                    pygame.draw.rect(pantalla,color_casilla,[(25) * columnas + 5,
                                 (25) * filas + 45,20,20])
                    if color_casilla == (0,255,0): #VERDE
                        pantalla.blit(bomba,[(25) * columnas + 5,
                                 (25) * filas + 45])
                        
        pygame.display.flip()
        
def tablero_colores(n,m): #creamos el tablero: introduciendo en las casillas donde haya barco el color marrón, y donde haya agua el color azul
    tablero = []
    for i in range(n):
        tablero.append([])
        for j in range(m):
            if (i,j) in l:
                tablero[i].append((128, 64, 0)) #MARRÓN
            else:
                tablero[i].append((0, 255, 255)) #AZUL AQUA
    return tablero



fichero = input('Introduzca el fichero que contiene la posición de las casillas que desea colocar: ')


def casillas_de_barcos(f): #funcion para leer el fichero donde tendremos colocados los barcos y poder sacar una lista de las posiciones
    archivo = open(f,'r')
    x = []
    s = []
    for linea in archivo:
        barco,posicion=linea.split(':')
        lista_pos= posicion.split(' ')
        s.append((barco,lista_pos))
        for i in lista_pos:
            a,b=i.split(',')
            fila = int(a)
            columna=int(b)
            x.append((fila,columna))
    return x,s
l = casillas_de_barcos(fichero)[0] #lista de posiciones en las que hay barco
k = casillas_de_barcos(fichero)[1] #lista de los barcos con sus respectivas posiciones


tablero = tablero_colores(20,42) #dimension del tablero



data={'tablero':tablero,'lanzar':False} #el elemento 'lanzar' nos servirá para publicar un mensaje de que podemos seguir lanzando bombas, es decir, colocando casillas

mqttc = Client(userdata=data)
mqttc.on_message = on_message
mqttc.enable_logger()

mqttc.connect("wild.mat.ucm.es")
mqttc.subscribe('clients/jugando')

mqttc.loop_start()


for i in k:
    barco = i[0]
    for j in i[1]:
        a,b=j.split(',')
        if '\n' in b:
            b=b[:-1] #para quitar el salto de linea
        mensaje = 'jugador2,'+barco+','+a+','+b #publicamos el jugador, los barcos y sus casillas para que el servidor pueda acceder a ellos.
        mqttc.publish('clients/tablero',mensaje)

        
while True: 
    if data['lanzar']:
        casilla = input('Lanzar bomba a la casilla: ')
        fila = int(casilla.split(',')[0])
        columna = int(casilla.split(',')[1])
        if fila >= 20 or columna >= 20: #comprobamos que ningún jugador se salga de rango en las casillas, para que no de error y podamos seguir jugando
            m='jugador2, se ha ido fuera de rango'
            mqttc.publish('clients/tablero',m) #para ello publicamos un mensaje de que se ha salido de rango y así poder volver a introducir una casilla
            print('Casilla fuera de rango')
        else:
            data['lanzar']=False
            m='jugador2'+','+casilla
            mqttc.publish('clients/tablero',m) #publicamos la casilla que el jugador ha introducido, y especificamos que jugador la ha introducido
