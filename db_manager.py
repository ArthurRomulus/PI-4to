#!/usr/bin/env python3
"""Gestor de base de datos SQLite para el proyecto.

Uso rapido:
  python db_manager.py tables
  python db_manager.py schema USERS
  python db_manager.py view USERS --limit 20
  python db_manager.py query "SELECT * FROM USERS LIMIT 5"
  python db_manager.py repl
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import sqlite3
import sys
from typing import Iterable, Sequence

from config import DATABASE


def _resolve_db_path(path: str) -> str:
    return os.path.abspath(path)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _print_table(rows: Sequence[Sequence[object]], headers: Sequence[str]) -> None:
    if not rows:
        print("(sin resultados)")
        return

    str_rows = [["" if v is None else str(v) for v in row] for row in rows]
    widths = [len(h) for h in headers]

    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(sep)
    print("| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(sep)
    for row in str_rows:
        print("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    print(sep)


def cmd_tables(conn: sqlite3.Connection) -> None:
    cur = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    rows = cur.fetchall()
    _print_table([(r["name"],) for r in rows], ["tabla"])


def cmd_schema(conn: sqlite3.Connection, table: str | None) -> None:
    if table:
        cur = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        )
        row = cur.fetchone()
        if not row:
            print(f"No existe la tabla: {table}")
            return
        print(row["sql"])
        return

    cur = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    rows = cur.fetchall()
    for row in rows:
        print(f"\n-- {row['name']} --")
        print(row["sql"])


def _build_select(table: str, where: str | None, order_by: str | None, limit: int) -> str:
    query = f"SELECT * FROM {table}"
    if where:
        query += f" WHERE {where}"
    if order_by:
        query += f" ORDER BY {order_by}"
    query += f" LIMIT {limit}"
    return query


def cmd_view(conn: sqlite3.Connection, table: str, where: str | None, order_by: str | None, limit: int) -> None:
    query = _build_select(table, where, order_by, limit)
    cur = conn.execute(query)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description] if cur.description else []
    _print_table([tuple(r[h] for h in headers) for r in rows], headers)


def cmd_query(conn: sqlite3.Connection, sql: str) -> None:
    cur = conn.execute(sql)
    lowered = sql.strip().lower()

    if lowered.startswith("select") or lowered.startswith("pragma"):
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description] if cur.description else []
        _print_table([tuple(r[h] for h in headers) for r in rows], headers)
    else:
        conn.commit()
        print(f"OK. Filas afectadas: {cur.rowcount}")


def cmd_export(conn: sqlite3.Connection, table: str, output: str, where: str | None, order_by: str | None, limit: int) -> None:
    query = _build_select(table, where, order_by, limit)
    cur = conn.execute(query)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description] if cur.description else []

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row[h] for h in headers])

    print(f"Exportado: {output} ({len(rows)} filas)")


def _print_help_repl() -> None:
    print(
        """
Comandos disponibles:
  tables
  schema [tabla]
  view <tabla> [limite]
  query <SQL>
  export <tabla> <archivo.csv> [limite]
  help
  exit
""".strip()
    )


def cmd_repl(conn: sqlite3.Connection) -> None:
    print("DB Manager interactivo. Escribe 'help' para ayuda.")
    while True:
        try:
            raw = input("db> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            return

        if not raw:
            continue

        if raw in {"exit", "quit"}:
            print("Saliendo...")
            return

        if raw == "help":
            _print_help_repl()
            continue

        parts = shlex.split(raw)
        cmd = parts[0].lower()

        try:
            if cmd == "tables":
                cmd_tables(conn)
            elif cmd == "schema":
                cmd_schema(conn, parts[1] if len(parts) > 1 else None)
            elif cmd == "view":
                if len(parts) < 2:
                    print("Uso: view <tabla> [limite]")
                    continue
                limit = int(parts[2]) if len(parts) > 2 else 20
                cmd_view(conn, parts[1], where=None, order_by=None, limit=limit)
            elif cmd == "query":
                if len(parts) < 2:
                    print("Uso: query <SQL>")
                    continue
                sql = raw[len("query") :].strip()
                cmd_query(conn, sql)
            elif cmd == "export":
                if len(parts) < 3:
                    print("Uso: export <tabla> <archivo.csv> [limite]")
                    continue
                limit = int(parts[3]) if len(parts) > 3 else 1000
                cmd_export(conn, parts[1], parts[2], where=None, order_by=None, limit=limit)
            else:
                print(f"Comando desconocido: {cmd}")
        except Exception as exc:
            print(f"Error: {exc}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestor SQLite del proyecto")
    parser.add_argument("--db", default=DATABASE, help="Ruta al archivo .db")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("tables", help="Listar tablas")

    p_schema = sub.add_parser("schema", help="Ver esquema")
    p_schema.add_argument("table", nargs="?", default=None, help="Nombre de tabla")

    p_view = sub.add_parser("view", help="Ver registros de una tabla")
    p_view.add_argument("table", help="Nombre de tabla")
    p_view.add_argument("--where", default=None, help="Condicion WHERE sin la palabra WHERE")
    p_view.add_argument("--order-by", default=None, help="ORDER BY sin la palabra ORDER BY")
    p_view.add_argument("--limit", type=int, default=20, help="Cantidad maxima de filas")

    p_query = sub.add_parser("query", help="Ejecutar SQL directo")
    p_query.add_argument("sql", help="Consulta SQL completa entre comillas")

    p_export = sub.add_parser("export", help="Exportar tabla a CSV")
    p_export.add_argument("table", help="Nombre de tabla")
    p_export.add_argument("output", help="Ruta archivo CSV de salida")
    p_export.add_argument("--where", default=None, help="Condicion WHERE sin la palabra WHERE")
    p_export.add_argument("--order-by", default=None, help="ORDER BY sin la palabra ORDER BY")
    p_export.add_argument("--limit", type=int, default=1000, help="Cantidad maxima de filas")

    sub.add_parser("repl", help="Modo interactivo")

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    db_path = _resolve_db_path(args.db)
    if not os.path.exists(db_path):
        print(f"No existe la base de datos: {db_path}")
        return 1

    try:
        conn = _connect(db_path)
    except Exception as exc:
        print(f"No se pudo abrir la base de datos: {exc}")
        return 1

    try:
        if args.command == "tables":
            cmd_tables(conn)
        elif args.command == "schema":
            cmd_schema(conn, args.table)
        elif args.command == "view":
            cmd_view(conn, args.table, args.where, args.order_by, args.limit)
        elif args.command == "query":
            cmd_query(conn, args.sql)
        elif args.command == "export":
            cmd_export(conn, args.table, args.output, args.where, args.order_by, args.limit)
        elif args.command == "repl":
            cmd_repl(conn)
        else:
            parser.print_help()
            return 1
        return 0
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
