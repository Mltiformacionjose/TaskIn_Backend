Feature: Conectividad con PostgreSQL

  Scenario: El backend establece una conexión válida
    Given que PostgreSQL está disponible
    And el backend tiene configurada una conexión válida
    When el backend solicita una conexión
    Then la conexión se establece correctamente
    And la consulta SELECT 1 devuelve un resultado válido
