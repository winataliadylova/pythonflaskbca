#import library 
from flask import Flask, jsonify, request, render_template
from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from
from sqlalchemy.sql import func
import os
import json

# Mendefinisikan app
app = Flask(__name__)

# Lokasi database
DATABASE_PATH = 'C:/Winata/Training Python/Final Project/invbar.db'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Swagger Configuration
app.config['SWAGGER'] = {
    'title': 'Data Investaris Barang API',
    'uiversion' : 3,
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/apispec_1.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/apidocs/'
}
swagger = Swagger(app)

db = SQLAlchemy(app)

# Model Data Master
class Item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable = False)
    category = db.Column(db.String(100), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    price = db.Column(db.DECIMAL(10,2), nullable = False)

# Model Data Transaction
class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'),nullable = False)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    quantity = db.Column(db.Integer, nullable = False)
    total_price = db.Column(db.DECIMAL(10,2), nullable = False)

@app.before_first_request
def create_table():
    db.create_all()

@app.route('/')
def index():    
    return render_template('index.html')

# Koneksi API untuk Barang
@app.route('/api/barang', methods=['POST'])
@swag_from('swagger_docs/create_data_barang.yaml')
def create_barang():
    # Mendapatkan data dari permintaan POST
    data = request.json

    # Membuat object Item
    new_item = Item(
        name = data['name'],
        category = data['category'],
        quantity = data['quantity'],
        price = data['price']
    )

    # Menyimpan object ke database
    db.session.add(new_item)
    db.session.commit()

    # Mengembalikan respons HTTP 201 Created
    return jsonify({'message' : 'Data barang baru berhasil ditambahkan'}), 201

@app.route('/api/barang/<int:item_id>', methods=['GET'])
@swag_from('swagger_docs/get_one_data_barang.yaml')
def get_one_barang(item_id):
    barang = Item.query.get(item_id)
    
    item = {
        'Item ID' : barang.item_id,
        'Name' : barang.name,
        'Category' : barang.category,
        'Quantity' : barang.quantity,
        'Price': barang.price
    }

    return jsonify({'message': f'Item: {item}'})

@app.route('/api/barang/display_all', methods=['GET'])
@swag_from('swagger_docs/get_all_data_barang.yaml')
def tampil_all_barang():
    barang_list = []
    try:
        # mengambil semua data barang dari database
        all_barang = Item.query.all()
        
        # Membuat daftar dari data karyawan untuk dikirimkan ke template
        for item in all_barang:
            print(item.item_id)
            item_data = {
                'item_id': item.item_id,
                'name': item.name,
                'category': item.category,
                'quantity': item.quantity,
                'price': item.price
            }
            barang_list.append(item_data)
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500
    finally:
        # Mengembalikan template dengan data karyawan jika tidak ada kesalahan
        if barang_list:
            return jsonify({'message' : f'Data barang berhasil ditampilkan {barang_list}'}), 200
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return jsonify({'message' : 'Data barang tidak di temukan'}), 404
    

@app.route('/api/barang/<int:item_id>', methods=['POST'])
@swag_from('swagger_docs/update_data_barang.yaml')
def update_barang(item_id):
    try:
        data = request.json
        barang = Item.query.get(item_id)
        
        barang.name = data['name']
        barang.category = data['category']
        barang.quantity = data['quantity']
        barang.price = data['price']

        db.session.commit()
        
        return jsonify({'message': f'Data barang berhasil di update'}), 200
    except Exception as e:
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500

@app.route('/api/barang/<int:item_id>', methods=['DELETE'])
@swag_from('swagger_docs/delete_data_barang.yaml')
def delete_barang(item_id):
    try:
        # Cari barang berdasarkan item_id
        barang_to_delete = Item.query.filter_by(item_id=item_id).first()

        # Jika barang ditemukan, hapus dari database
        if barang_to_delete:
            transaksi = Transaction.query.filter_by(item_id=item_id).all()
            for trans in transaksi:
                db.session.delete(trans)
            db.session.delete(barang_to_delete)
            db.session.commit()

            return jsonify({'message' : f'Data Barang dengan ID {item_id} berhasil dihapus'}), 200
        else:
            return jsonify({'message' : f'Data Barang dengan ID {item_id} tidak ditemukan'}), 404

    except Exception as e:
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500

# Koneksi API untuk transaksi
@app.route('/api/transaction', methods=['POST'])
@swag_from('swagger_docs/create_data_transaction.yaml')
def create_transaction():
    try:
        list_item = query_all_barang()
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500
    finally:
         # Mengembalikan template dengan data barang jika tidak ada kesalahan
        if list_item:
            data = request.json
            int_quantity = int(data['quantity'])

            item = Item.query.get(data['item_id'])
            if item:
                # Membuat object item baru
                total_price = int_quantity * item.price
                new_trans = Transaction(
                    item_id = data['item_id'],
                    quantity = data['quantity'],
                    total_price = total_price
                )

                item.quantity -= int_quantity
                
                # Masukkan ke Database
                db.session.add(new_trans)
                db.session.commit()
            else:
                return jsonify({'message' : f'Data Barang dengan ID {item.item_id} tidak ditemukan'}), 404
            
            return jsonify({'message' : 'Data transaksi baru berhasil ditambahkan'}), 201
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return jsonify({'message' : 'Tidak ada dapat membuat transaksi karena tidak ada barang'}), 404
    pass

@app.route('/api/transaction/display_all', methods=['GET'])
@swag_from('swagger_docs/get_all_data_transaction.yaml')
def tampil_all_transaction():
    try:
        list_transaksi = query_all_transaksi()
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500
    finally:
         # Mengembalikan template dengan data barang jika tidak ada kesalahan
        if list_transaksi:
             return jsonify({'message' : f'Data transaksi berhasil ditampilkan {list_transaksi}'}), 200
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return jsonify({'message' : 'Data transaksi tidak di temukan'}), 404

@app.route('/api/transaction/<int:transaction_id>', methods=['GET'])
@swag_from('swagger_docs/get_one_data_transaction.yaml')
def get_one_transaction(transaction_id):
    try:
        transaksi = Transaction.query.get(transaction_id)
        item = Item.query.get(transaksi.item_id)

        Object = {
            'Transaction ID' : transaksi.transaction_id,    
            'Item ID' : transaksi.item_id,
            'Name' : item.name,
            'Category' : item.category,
            'Quantity' : transaksi.quantity,
            'Total Price': transaksi.total_price
        }

        return jsonify({'message': f'Transaksi: {Object}'})
    except Exception as e:
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500

@app.route('/api/transaction/<int:transaction_id>', methods=['DELETE'])
@swag_from('swagger_docs/delete_data_transaction.yaml')
def delete_transaksi(transaction_id):
    try:
        # Cari transaksi berdasarkan transaction_id
        transaction_to_delete = Transaction.query.filter_by(transaction_id=transaction_id).first()

        # Jika transaksi ditemukan, hapus dari database
        if transaction_to_delete:
            item = Item.query.get(transaction_to_delete.item_id)
            item.quantity += transaction_to_delete.quantity

            db.session.delete(transaction_to_delete)
            db.session.commit()

            return jsonify({'message' : f'Data transaksi dengan ID {transaction_id} berhasil dihapus'}), 200
        else:
            return jsonify({'message' : f'Data transaksi dengan ID {transaction_id} tidak ditemukan'}), 404

    except Exception as e:
        return jsonify({'message': f"Terjadi kesalahan: {e}"}), 500

def query_all_barang():
    barang_list = []
    all_barang = Item.query.all()

    # Membuat daftar dari data barang untuk dikirimkan ke template
    for item in all_barang:
        item_data = {
            'item_id': item.item_id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'price': item.price
        }
        barang_list.append(item_data)

    return barang_list

def query_all_transaksi():
    transaksi_list = []
    all_transaksi = Transaction.query.all()
    all_barang = Item.query.all()

    # Membuat daftar dari data transaksi untuk dikirimkan ke template
    for barang in all_barang:
        for item in all_transaksi:
            if item.item_id == barang.item_id:
                item_data = {
                    'transaction_id': item.transaction_id,
                    'item_id': item.item_id,
                    'name': barang.name,
                    'category': barang.category,
                    'date': item.date,
                    'quantity': item.quantity,
                    'total_price': item.total_price
                }
                transaksi_list.append(item_data)

    return transaksi_list

# Function untuk Users
@app.route('/input/barang', methods=['GET', 'POST'])
def input_data_barang():
    if request.method == 'POST':
        nama_item = request.form.get('name')
        category = request.form.get('category')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        if not nama_item or not category or not quantity or not price:
            return render_template('createdatabarang.html', error="Semua field wajib diisi!")
        
        # Membuat object item baru
        new_item = Item(
            name = nama_item,
            category = category,
            quantity = quantity,
            price = price
        )

        # Masukkan ke Database
        db.session.add(new_item)
        db.session.commit()
        
        return render_template('confirmation.html', tipe="Barang")
    else:
        return render_template('createdatabarang.html')

@app.route('/barang/display_all', methods=['GET'])
def display_all_barang():
    try:
        list_item = query_all_barang()
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return render_template('error.html', pesan="Terjadi kesalahan saat mengambil data barang: {}".format(str(e)), link="/"), 500
    finally:
         # Mengembalikan template dengan data barang jika tidak ada kesalahan
        if list_item:
            return render_template('displayall.html', list_barang=list_item)
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return render_template('error.html', pesan="Tidak ada data barang yang dapat ditampilkan", link="/"), 404

@app.route('/barang/updatedata', methods=['GET', 'POST'])
def update_data_barang():
    
    if request.method == 'POST':
        nama_item = request.form.get('name')
        item = Item.query.filter(Item.name.like(f"%{nama_item}%")).all()
        return render_template('updatedatabarang.html', list_data = item)
    else:
        return render_template('updatedatabarang.html')

@app.route('/barang/update_data', methods=['POST'])
def update_data():
    try:
        #Ambil data dari form
        item_id = request.form.get('item_id')
        name = request.form.get('name')
        category = request.form.get('category')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        # Temukan karyawan berdasarkan id_karyawan
        item = Item.query.get(item_id)

        if not item:
            return jsonify({'message' : 'Karyawan tidak ditemukan'}), 404

        # Update Data Karyawan
        item.name = name
        item.category = category
        item.quantity = quantity
        item.price = price

        db.session.commit()

        return redirect(url_for('display_all_barang'))
    except Exception as e:
        return jsonify({'message' : f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/input/transaction', methods=['POST', 'GET'])
def input_data_transaksi():
    try:
        list_item = query_all_barang()
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return render_template('error.html', pesan="Terjadi kesalahan saat mengambil data barang: {}".format(str(e)), link="/"), 500
    finally:
         # Mengembalikan template dengan data barang jika tidak ada kesalahan
        if list_item:
            if request.method == 'POST':
                item_id = request.form.get('item_id')
                quantity = request.form.get('quantity')
                int_quantity = int(quantity)

                item = Item.query.get(item_id)
                if item:
                    # Membuat object item baru
                    total_price = int_quantity * item.price
                    new_trans = Transaction(
                        item_id = item_id,
                        quantity = quantity,
                        total_price = total_price
                    )

                    item.quantity -= int_quantity
                    
                    # Masukkan ke Database
                    db.session.add(new_trans)
                    db.session.commit()
                else:
                    
                    return render_template('error.html', pesan=f"Barang dengan ID {item_id} tidak ditemukan",link="/input/transaction")
                
                return render_template('confirmation.html', tipe="Transaksi")
            else:
                return render_template('createdatatransaksi.html', list_barang=list_item)
            
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return render_template('error.html', pesan="Tidak ada dapat membuat transaksi karena tidak ada barang", link="/"), 404

@app.route('/transaction/display_all', methods=['GET'])
def display_all_transaction():
    try:
        list_transaksi = query_all_transaksi()
    except Exception as e:
        # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika terjadi kesalahan
        return render_template('error.html', pesan="Terjadi kesalahan saat mengambil data transaksi: {}".format(str(e)), link="/"), 500
    finally:
         # Mengembalikan template dengan data barang jika tidak ada kesalahan
        if list_transaksi:
            return render_template('displayall_transaksi.html', list_transaction=list_transaksi)
        else:
            # Mengembalikan pesan kesalahan dalam Bahasa Indonesia jika tidak ada data dalam data base
            return render_template('error.html', pesan="Tidak ada data transaksi yang dapat ditampilkan", link="/"), 404

if __name__ == '__main__':
    app.run(debug=True, port=5030)

