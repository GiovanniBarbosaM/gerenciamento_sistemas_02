from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flasgger import Swagger
from flask_caching import Cache
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost:5432/seu_banco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta'  # Mude isso para uma chave segura
db = SQLAlchemy(app)
jwt = JWTManager(app)
swagger = Swagger(app)
cache = Cache(app)

# Modelo de Produto
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Produto {self.nome}, Quantidade {self.quantidade}>"

# Modelo de Venda
class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade_vendida = db.Column(db.Integer, nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)

    produto = db.relationship('Produto', backref=db.backref('vendas', lazy=True))

# Modelo de Entrega
class Entrega(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    data_entrega = db.Column(db.DateTime, nullable=False)
    endereco_entrega = db.Column(db.String(200), nullable=False)

# Schema de Validação
class ProdutoSchema(Schema):
    nome = fields.Str(required=True)
    categoria = fields.Str(required=True)
    quantidade = fields.Int(required=True, validate=lambda x: x >= 0)
    preco = fields.Float(required=True, validate=lambda x: x >= 0)
    localizacao = fields.Str(required=True)

produto_schema = ProdutoSchema()

# Criar o banco de dados
with app.app_context():
    db.create_all()

# Funções Auxiliares
def get_produtos_list():
    return Produto.query.all()

def produto_to_dict(produto):
    return {
        'id': produto.id,
        'nome': produto.nome,
        'categoria': produto.categoria,
        'quantidade': produto.quantidade,
        'preco': produto.preco,
        'localizacao': produto.localizacao
    }

# Rotas
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # Verifique se as credenciais estão corretas (substitua pela sua lógica)
    if username == 'admin' and password == 'senha':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Credenciais inválidas"}), 401

@app.route('/api/produtos', methods=['POST'])
@jwt_required()
def cadastrar_produto():
    """
    Cadastrar um novo produto
    ---
    parameters:
      - name: produto
        in: body
        required: true
        schema:
          id: Produto
          properties:
            nome:
              type: string
              description: Nome do produto
              required: true
            categoria:
              type: string
              description: Categoria do produto
              required: true
            quantidade:
              type: integer
              description: Quantidade do produto
              required: true
            preco:
              type: number
              format: float
              description: Preço do produto
              required: true
            localizacao:
              type: string
              description: Localização do produto
              required: true
    responses:
      201:
        description: Produto cadastrado com sucesso
    """
    data = request.get_json()
    try:
        validated_data = produto_schema.load(data)
        novo_produto = Produto(**validated_data)
        db.session.add(novo_produto)
        db.session.commit()
        return jsonify({"message": "Produto cadastrado com sucesso!"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@app.route('/api/produtos', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def listar_produtos():
    """
    Listar todos os produtos
    ---
    parameters:
      - name: nome
        in: query
        type: string
      - name: categoria
        in: query
        type: string
    responses:
      200:
        description: Lista de produtos
    """
    nome = request.args.get('nome')
    categoria = request.args.get('categoria')
    query = Produto.query

    if nome:
        query = query.filter(Produto.nome.ilike(f"%{nome}%"))
    if categoria:
        query = query.filter(Produto.categoria.ilike(f"%{categoria}%"))

    produtos = query.all()
    return jsonify([produto_to_dict(p) for p in produtos])

@app.route('/api/produtos/<int:id>', methods=['DELETE'])
def remover_produto(id):
    produto = Produto.query.get_or_404(id)
    db.session.delete(produto)
    db.session.commit()
    return jsonify({"message": "Produto removido com sucesso!"}), 204

@app.route('/api/produtos/<int:id>', methods=['PUT'])
def atualizar_produto(id):
    produto = Produto.query.get_or_404(id)
    data = request.get_json()
    try:
        validated_data = produto_schema.load(data)
        for key, value in validated_data.items():
            setattr(produto, key, value)
        db.session.commit()
        return jsonify({"message": "Produto atualizado com sucesso!"}), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

@app.route('/api/relatorios', methods=['GET'])
def relatorio_estoque():
    produtos_baixo_estoque = Produto.query.filter(Produto.quantidade < 10).all()  # Estoque baixo
    produtos_excesso_estoque = Produto.query.filter(Produto.quantidade > 100).all()  # Excesso de estoque

    return jsonify({
        'baixo_estoque': [{
            'nome': p.nome,
            'quantidade': p.quantidade,
            'localizacao': p.localizacao
        } for p in produtos_baixo_estoque],
        'excesso_estoque': [{
            'nome': p.nome,
            'quantidade': p.quantidade,
            'localizacao': p.localizacao
        } for p in produtos_excesso_estoque],
    })

@app.route('/api/relatorio_produtos', methods=['GET'])
def relatorio_produtos():
    produtos = Produto.query.all()
    relatorio = [{"nome": produto.nome, "quantidade": produto.quantidade} for produto in produtos]
    total_estoque = sum(produto.quantidade for produto in produtos)

    return jsonify({"produtos": relatorio, "total_estoque": total_estoque})

@app.route('/api/produto/<string:nome>', methods=['GET'])
def produto_especifico(nome):
    produto = Produto.query.filter_by(nome=nome).first()
    if produto:
        return jsonify(produto_to_dict(produto))
    else:
        return jsonify({"error": "Produto não encontrado"}), 404

@app.route('/api/relatorios/vendas', methods=['GET'])
def relatorio_vendas():
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Filtrar vendas no período especificado
    vendas = Venda.query.filter(Venda.data_venda.between(data_inicial, data_final)).all()
    relatorio = [{
        'produto': v.produto.nome,
        'quantidade_vendida': v.quantidade_vendida,
        'data_venda': v.data_venda.isoformat()
    } for v in vendas]
    
    return jsonify(relatorio)

@app.route('/api/produtos/<int:id>/atualizar_estoque', methods=['PUT'])
def atualizar_estoque(id):
    produto = Produto.query.get_or_404(id)
    data = request.get_json()
    quantidade = data.get('quantidade')
    
    if quantidade is not None:
        produto.quantidade += quantidade
        db.session.commit()
        return jsonify({"message": "Estoque atualizado com sucesso!"}), 200
    
    return jsonify({"error": "Quantidade inválida!"}), 400

@app.route('/api/entregas', methods=['POST'])
def agendar_entrega():
    data = request.get_json()
    nova_entrega = Entrega(
        produto_id=data['produto_id'],
        data_entrega=data['data_entrega'],
        endereco_entrega=data['endereco_entrega']
    )
    db.session.add(nova_entrega)
    db.session.commit()
    return jsonify({"message": "Entrega agendada com sucesso!"}), 201

if __name__ == '__main__':
    app.run(debug=True)
