Consome a interface do [[Adapter do banco de dados]] para realizar as operações relacionadas aos  pedidos

### obter(self, pedido_id: int, com_itens: bool = True) -> Pedido | None

Recebe um id de pedido e um flag para informar se é preciso trazer os itens junto, com esses dados ele consulta o banco e traz o registro correspondente ao id, se a flag for true busca os itens do pedido também.

### _filtro(obra: str | None, status_atual: str | None, user_id: int | None) -> tuple\[str, list\]


usando os dados da entrada cria o sentença do where da consulta


