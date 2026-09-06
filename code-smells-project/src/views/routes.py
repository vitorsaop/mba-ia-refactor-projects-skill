from flask import Blueprint

from src.controllers import (
    produto_controller,
    usuario_controller,
    pedido_controller,
    relatorio_controller,
    home_controller,
    admin_controller,
)

produto_bp = Blueprint("produtos", __name__)
produto_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_varios, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto_controller.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produto_controller.atualizar, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produto_controller.deletar, methods=["DELETE"])

usuario_bp = Blueprint("usuarios", __name__)
usuario_bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuario_controller.buscar, methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

pedido_bp = Blueprint("pedidos", __name__)
pedido_bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar, methods=["POST"])
pedido_bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos, methods=["GET"])
pedido_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_controller.listar_por_usuario, methods=["GET"])
pedido_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_controller.atualizar_status, methods=["PUT"])

relatorio_bp = Blueprint("relatorios", __name__)
relatorio_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.vendas, methods=["GET"])
relatorio_bp.add_url_rule("/health", "health_check", relatorio_controller.health, methods=["GET"])

home_bp = Blueprint("home", __name__)
home_bp.add_url_rule("/", "index", home_controller.index, methods=["GET"])

admin_bp = Blueprint("admin", __name__)
admin_bp.add_url_rule("/admin/reset-db", "reset_database", admin_controller.reset_database, methods=["POST"])
admin_bp.add_url_rule("/admin/query", "executar_query", admin_controller.executar_query, methods=["POST"])

ALL_BLUEPRINTS = (produto_bp, usuario_bp, pedido_bp, relatorio_bp, home_bp, admin_bp)
