"""
Publica en: clients/jugando

Recibe mensaje de: clients/tablero

"""

from paho.mqtt.client import Client 
from multiprocessing import Process
import paho.mqtt.publish as publish


def on_message(mqttc,userdata,msg):
   mensaje = str(msg.payload)[2:-1]
   if datos['fichas'] != -1:
       j,b,fila,columna = mensaje.split(',')
       f=int(fila)
       c=int(columna)
       if j == 'jugador1':
           barcos1[b].append((f,c)) #añadimos las casillas al diccionario de los barcos
           datos['tablero1'][f][c] =1 #colocamos la ficha del barco en el diccionario del tablero cambiando 0 (cuando no hay barco) por 1 (cuando hay barco)
           datos['fichas'] -= 1
       else:
           barcos2[b].append((f,c))
           datos['tablero2'][f][c] =1
           datos['fichas'] -= 1
       if datos['fichas'] == 0: #cuando todas las fichas estan colocadas
           publicar = Process(target=on_publish,args=('Comenzamos',))
           publicar.start()
           datos['fichas'] -=1
   else:
       ataque(mensaje) #una vez colocadas todas, podremos empezar el juego
       
       
def on_publish(mensaje): #función que usaremos para publicar los mensajes.
    print(mensaje)
    publish.single('clients/jugando', payload=mensaje, hostname="wild.mat.ucm.es")


def ataque(mensaje):
    if mensaje == 'jugador1, se ha ido fuera de rango': #cuando el jugador mete coordenadas fuera de rango, por ejemplo: 24,3
        publi = Process(target=on_publish,args=(mensaje,))
        publi.start()
    elif mensaje == 'jugador2, se ha ido fuera de rango':
        publi = Process(target=on_publish,args=(mensaje,))
        publi.start()
    else:
        jugador,fila,columna = mensaje.split(',') #el jugador introduce una casilla, y procedemos a ver qué hay en esa casilla:
        f = int(fila)
        c=int(columna)
        if jugador == 'jugador1': #si ha introducido la casilla el jugador 1, la bomba irá al tablero del jugador2
            tablero = 'tablero2'
        else:
            tablero = 'tablero1'  #y viceversa
        info = datos[tablero][f][c] #cogemos del diccionario del tablero la información de esa casilla, viendo si hay barco o no
        if info == 0: #no hay barco
            datos[tablero][f][c] = 2 #cambiamos el 0 por 2 para indicar que ya hemos marcado esa casilla.
            mensaje=jugador+','+' ha tirado al agua en la casilla: '+fila+','+columna 
            publi = Process(target=on_publish,args=(mensaje,)) #mandamos mensaje de que se ha tocado AGUA y la casilla.
            publi.start()
            
        elif info == 1: #hay barco
            datos[tablero][f][c] = 2 #igual que antes, cambiamos el 0 por 2 para indicar que ya hemos marcado esa casilla.
            hundido=tocado_hundido(f,c,jugador) #comprobamos si al tocar el barco, lo hemos hundido ya o no
            mensaje=jugador+','+' ha tocado barco en la casilla: '+fila+','+columna+','+hundido 
            publi = Process(target=on_publish,args=(mensaje,)) #mandamos mensaje de que se ha TOCADO BARCO incluyendo la información de si ha sido hundido o no, y la casilla
            publi.start()
            
            if jugador == 'jugador1':
                barcos = barcos2
            else:
                barcos= barcos1
            
            if len(barcos) == 0: #en caso de que el diccionario de barcos del contrincante se quede vacía, es porque ya hemos hundido todos sus barcos y por tanto habremos ganado.
                mensaje = 'HA GANADO EL'+' '+jugador
                publicar = Process(target=on_publish,args=(mensaje,)) #mandamos mensaje de que hemos ganado y finalizaremos desde el archivo del ganador
                publicar.start()
            else:
                pass
            
        else: #si info == 2, será porque ya hemos puesto esa casilla antes, y por tanto mandaremos mensaje de que ya la hemos marcado para poder introducir otra
            mensaje=jugador+','+' ya has MARCADO esa casilla antes'
            publi = Process(target=on_publish,args=(mensaje,)) #mandamos el mensaje
            publi.start()

            
    
def tocado_hundido(f,c,jugador): #para ver si el barco que hemos tocado está hundido o no
    if jugador=='jugador1': #si somos el jugador 1, tendremos que ver el diccionario de barcos del jugador 2, que son los barcos que estamos bombardeando
        barcos=barcos2
    else:
        barcos=barcos1 #y viceversa
    casilla=(f,c) 
    b=False
    for barco in barcos.keys():
        if casilla in barcos[barco]: #si la casilla que hemos puesto, está en el diccionario de barcos del otro jugador
            barcos[barco].remove(casilla) #eliminamos esa casilla del diccionario
            solucion = barco
            if len(barcos[barco])==0: #y si ese barco queda vacío, es porque lo hemos hundido entero.
                b = True
    if b:
        barcos.pop(solucion) #eliminamos ese barco del diccionario de barcos
        hundido =' y lo ha HUNDIDO'
        m = jugador+' ha hundido un barco'
        pub = Process(target=on_publish,args=(m,)) #mandamos mensaje de que ya se ha hundido un barco
        pub.start()
    else:
        hundido =' pero NO lo ha hundido'
    return(hundido)

  

def tablero(n): #creamos el tablero vacio y lo rellenamos en la funcion on_message()
    l = []
    for x in range(n):
        s= []
        for x in range(n):
            s.append(0)
        l.append(s)
    return l


datos={'tablero1':tablero(20),'tablero2':tablero(20),'fichas': 54} #empezamos con 54 fichas pa colocar, así cuando en on_message() se llegue a datos['fichas']==0,
                                                                   #sabremos que están todas las posiciones de barcos marcadas y podremos comenzar a jugar.
barcos2={'b1':[],'b2':[],'b3':[],'b4':[],'b5':[],'b6':[]}
barcos1={'b1':[],'b2':[],'b3':[],'b4':[],'b5':[],'b6':[]}


mqttc = Client(userdata=(datos,barcos1,barcos2))
mqttc.on_message = on_message
mqttc.enable_logger()

mqttc.connect("wild.mat.ucm.es")
mqttc.subscribe('clients/tablero')
mqttc.loop_forever()