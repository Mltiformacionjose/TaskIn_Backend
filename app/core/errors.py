"""Gestión centralizada de errores de la API."""


class DatabaseConnectionError(RuntimeError):
    """Error controlado al establecer o verificar la conexión con PostgreSQL.

    El mensaje es apto para mostrarse sin revelar la URL de conexión ni
    credenciales. La causa original queda encadenada para su depuración.
    """

    def __init__(
        self,
        message: str = "No se pudo establecer conexión con la base de datos.",
    ) -> None:
        super().__init__(message)
