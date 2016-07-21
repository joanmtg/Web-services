#!/usr/bin/python

# Librerias requeridas para correr aplicaciones basadas en Flask
from flask import Flask, jsonify, abort, make_response, request
import subprocess

app = Flask(__name__)

# Web service que se invoca al momento de ejecutar el comando
# curl http://localhost:5000

@app.route('/',methods = ['GET'])
def index():
        return "Hola"

# Manejador de errores con codigo 404

@app.errorhandler(404)
def not_found(error):
 return make_response(jsonify({'error': 'Not found'}), 404)


# Este metodo retorna la lista de sistemas operativos soportados por VirtualBox
# Los tipos de sistemas operativos soportados deben ser mostrados al ejecutar 
# el comando:
# curl http://localhost:5000/vms/ostypes

@app.route('/vms/ostypes',methods = ['GET'])
def listarOS():	
	osTypes = subprocess.check_output(['VBoxManage', 'list', 'ostypes'])
			
        return "Sistemas Operativos:\n%s"%(osTypes)


# Este metodo retorna la lista de maquinas asociadas con un usuario al ejecutar
# el comando:
# curl http://localhost:5000/vms

@app.route('/vms',methods = ['GET'])
def listarVM():
	userMachines = subprocess.check_output(['VBoxManage', 'list', 'vms'])
	
	return "Estas son las maquinas virtuales del usuario:\n%s\n"%(userMachines)
	

# Este metodo retorna aquellas maquinas que se encuentran en ejecucion al 
# ejecutar el comando:
# curl http://localhost:5000/vms/running

@app.route('/vms/running',methods = ['GET'])
def listarVMrunning():
	exeMachines = subprocess.check_output(['VBoxManage', 'list', 'runningvms'])
	
	return "Estas son las maquinas virtuales en ejecucion: \n%s\n"%(exeMachines)
        	


# Este metodo muestra la informacion de una maquina virtual en especifico al
# ejecutar el comando:
# curl http://localhost:5000/vms/info/<nombre-Maquina>

@app.route('/vms/info/<nombre>', methods = ['GET'])
def mostrarInformacionVM(nombre):
	
	output= ""
	existe = existeMaquina(nombre)
				
	if (existe == 0):
		abort(404)
		
	comando1 = "VBoxManage showvminfo %s | grep 'Number of CPUs' "%(nombre)
	comando2 = "VBoxManage showvminfo %s | grep 'Memory size' "%(nombre)
	comando3 = "VBoxManage showvminfo %s | grep 'NIC' | grep -v 'disabled' | grep -v 'Settings' | cut -d ',' -f 2 | cut -d ':' -f 2"%(nombre)

        cpu = subprocess.check_output(comando1, shell = True)
	memory  = subprocess.check_output(comando2, shell = True)
	interfacesHabilitadas = subprocess.check_output(comando3, shell=True)

	interfaces = interfacesHabilitadas.split("\n")
	interfaces.remove("")

	conteoInterfaces = len(interfaces)
		
	output = "\nMaquina virtual: %s \n%s%s \nInterfaces de red: %s\n" %(nombre, cpu, memory, conteoInterfaces)

	for i in range(conteoInterfaces):
	    output+= "Interfaz de red %s: %s\n"%(i+1,interfaces[i])

	return output

# Este metodo se encarga de crear una nueva maquina virtual, recibiendo parametros por
# medio del metodo POST al ejecutar el comando:
# curl -i -H "Content-Type: application/json" -X POST -d '{"nombre": <nombre>, "RAM": <RAM>, "nucleos": <nucleos>}' "http://localhost:5000/vms"

@app.route('/vms', methods=['POST'])
def crearVM():

	if not request.json or not 'nombre'  or not 'RAM' or not 'nucleos' in request.json:
	  abort(400)
	
	nombre = request.json['nombre']
	RAM = request.json['RAM']
	nucleos = request.json['nucleos']
		
        comando1 = "VBoxManage createhd --filename %s.vdi --size 32768"%(nombre)
        comando2 = "VBoxManage createvm --name %s --ostype 'Ubuntu' --register"%(nombre)
        comando3 = "VBoxManage storagectl %s --name 'SATA Controller' --add sata --controller IntelAHCI"%(nombre)
        comando4 = "VBoxManage storageattach %s --storagectl 'SATA Controller' --port 0 --device 0 --type hdd --medium %s.vdi"%(nombre,nombre)
        comando5 = "VBoxManage storagectl %s --name 'IDE Controller' --add ide"%(nombre)
        comando6 = "VBoxManage modifyvm %s --ioapic on"%(nombre)
        comando7 = "VBoxManage modifyvm %s --boot1 dvd --boot2 disk --boot3 none --boot4 none"%(nombre)
        comando8 = "VBoxManage modifyvm %s --memory %s --vram 128"%(nombre,RAM)
        comando9 = "VBoxManage modifyvm %s --cpus %s"%(nombre,nucleos)

        subprocess.check_output(comando1, shell = True)
        subprocess.check_output(comando2, shell = True)
        subprocess.check_output(comando3, shell = True)
        subprocess.check_output(comando4, shell = True)
        subprocess.check_output(comando5, shell = True)
        subprocess.check_output(comando6, shell = True)
        subprocess.check_output(comando7, shell = True)
        subprocess.check_output(comando8, shell = True)
        subprocess.check_output(comando9, shell = True)
	

	return jsonify({'result': True})

	
# Este metodo se encarga de eliminar una maquina virtual del usuario en especifico
# al ejecutar el comando:
# curl -X DELETE http://localhost:5000/vms/<nombre-Maquina>

@app.route('/vms/<nombre>', methods=['DELETE'])
def borrarVM(nombre):

	existe = existeMaquina(nombre)

	if (existe == 0):
		abort(404)

        comando = "VBoxManage unregistervm %s --delete"%(nombre)
        subprocess.check_output(comando, shell = True)

	return jsonify({'result': True})


# Metodo axiliar que, dado un nombre, retorna 1 si el usuario tiene una maquina virtual
# con dicho nombre o 0 en el caso contrario. Este metodo es util para realizar
# validaciones antes de llevar a cabo un procedimiento que requiera
# la existencia de una maquina virtual con un nombre especifico

def existeMaquina(nombre):

	comando = "VBoxManage list vms | awk '{print $1}'"
        resultado = subprocess.check_output(comando, shell = True)

        maquinas = resultado.split("\n")
        maquinas.remove("")

        existe = 0

        for maquina in maquinas:
                string = maquina.replace('"', '')
                if (string == nombre):
                        existe = 1
                        break

	return existe


if __name__ == '__main__':
	app.run(debug = True, host='0.0.0.0')


