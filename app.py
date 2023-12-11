from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from werkzeug.utils import secure_filename

import os
import time


app = Flask(__name__)
CORS(app)  
class Catalogo:
   
    def __init__(self, host, port, user, password, database):
        
        self.conn = mysql.connector.connect(
          host=host,
            user=user,
            port=port,
            password=password,
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
           
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

     
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT,
            descripcion VARCHAR(255) NOT NULL,
            cantidad INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen_url VARCHAR(255),
            proveedor INT(4))''')
        self.conn.commit()

   
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)
        
    
    def agregar_producto(self, id, descripcion, cantidad, precio, imagen, proveedor):
        
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {id}")
        producto_existe = self.cursor.fetchone()
        if producto_existe:
            return False

        
        sql = "INSERT INTO productos (codigo, descripcion, cantidad, precio, imagen_url, proveedor) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (id, descripcion, cantidad, precio, imagen, proveedor)

        self.cursor.execute(sql, valores)        
        self.conn.commit()
        return True

    
    def consultar_producto(self, id):
       
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {id}")
        return self.cursor.fetchone()

    
    def modificar_producto(self, id, nueva_descripcion, nueva_cantidad, nuevo_precio, nueva_imagen, nuevo_proveedor):
        sql = "UPDATE productos SET descripcion = %s, cantidad = %s, precio = %s, imagen_url = %s, proveedor = %s WHERE codigo = %s"
        valores = (nueva_descripcion, nueva_cantidad, nuevo_precio, nueva_imagen, nuevo_proveedor, id)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

 
    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()
        return productos

    
    def eliminar_producto(self, id):
        
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {id}")
        self.conn.commit()
        return self.cursor.rowcount > 0

 
    def mostrar_producto(self, id):
        
        producto = self.consultar_producto(id)
        if producto:
            print("-" * 40)
            print(f"Id.....: {producto['id']}")
            print(f"Descripción: {producto['descripcion']}")
            print(f"Cantidad...: {producto['cantidad']}")
            print(f"Precio.....: {producto['precio']}")
            print(f"Imagen.....: {producto['imagen_url']}")
            print(f"Proveedor..: {producto['proveedor']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")



""" catalogo = Catalogo(host='localhost', port='3307', user='root', password='', database='miapp') """
catalogo = Catalogo(host='franco97.mysql.pythonanywhere-services.com',port=3307, user='franco97', password='020597', database='franco97$miapp')

catalogo.agregar_producto(1, "Camiseta del Chelsea",11, 55000, "chelsea.jpg",1)
catalogo.agregar_producto(2, "Camiseta del Inter",11, 80000, "Inter.jpg",1)
catalogo.agregar_producto(3, "Camiseta del Liverpool",11, 37000, "Liverpool.jpg",1)
catalogo.agregar_producto(4, "Camiseta del Newcastle",11, 35000, "Newcastle.jpg",1)
catalogo.agregar_producto(5, "Camiseta del PSG",11, 90000, "PSG.jpg",1)





RUTA_DESTINO = '/home/franco97/mysite/static/imagenes'

@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    return jsonify(productos)



@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(id):
    producto = catalogo.consultar_producto(id)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404



@app.route("/productos", methods=["POST"])

def agregar_producto():
   
    id = request.form['id']
    descripcion = request.form['descripcion']
    cantidad = request.form['cantidad']
    precio = request.form['precio']
    imagen = request.files['imagen']
    proveedor = request.form['proveedor']  
    nombre_imagen=""

   
    producto = catalogo.consultar_producto(id)
    if not producto: 
        nombre_imagen = secure_filename(imagen.filename) 
        nombre_base, extension = os.path.splitext(nombre_imagen) 
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" 
        
     
     
        if  catalogo.agregar_producto(id, descripcion, cantidad, precio, nombre_imagen, proveedor):
            imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

        
            return jsonify({"mensaje": "Producto agregado correctamente.", "imagen": nombre_imagen}), 201
        else:
            
            return jsonify({"mensaje": "Error al agregar el producto."}), 500

    else:
        
        return jsonify({"mensaje": "Producto ya existe."}), 400
    

@app.route("/productos/<int:id>", methods=["PUT"])

def modificar_producto(id):
   
    nueva_descripcion = request.form.get("descripcion")
    nueva_cantidad = request.form.get("cantidad")
    nuevo_precio = request.form.get("precio")
    nuevo_proveedor = request.form.get("proveedor")
    imagen = request.files['imagen']

   
    nombre_imagen = secure_filename(imagen.filename) 
    nombre_base, extension = os.path.splitext(nombre_imagen) 
    nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" 

  
    producto = producto = catalogo.consultar_producto(id)
    if producto: 
        imagen_vieja = producto["imagen_url"]
        
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

       
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
    
    
    if catalogo.modificar_producto(id, nueva_descripcion, nueva_cantidad, nuevo_precio, nombre_imagen, nuevo_proveedor):
        
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

      
        return jsonify({"mensaje": "Producto modificado"}), 200
    else:
        
        return jsonify({"mensaje": "Producto no encontrado"}), 403




@app.route("/productos/<int:codigo>", methods=["DELETE"])

def eliminar_producto(codigo):
    
    producto = catalogo.consultar_producto(codigo)
    if producto: 
        imagen_vieja = producto["imagen_url"]
        
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

        
        if catalogo.eliminar_producto(codigo):
            
            return jsonify({"mensaje": "Producto eliminado"}), 200
        else:
         
            return jsonify({"mensaje": "Error al eliminar el producto"}), 500
    else:
   
        return jsonify({"mensaje": "Producto no encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)