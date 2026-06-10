from django.db import connection

from filesystem.models import Node


class NodeRepository:
    # Could be done with Django orm, but because of Big O is done with raw query (time complexity is linear)
    def find_node_parent_chain(self, node: Node)->str:
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE ancestors AS (
                    SELECT id, original_name, parent_id, 0 AS depth
                    FROM nodes
                    WHERE id = %s

                    UNION ALL

                    SELECT n.id, n.original_name, n.parent_id, a.depth + 1
                    FROM nodes n
                    INNER JOIN ancestors a ON n.id = a.parent_id
                )
                SELECT original_name FROM ancestors ORDER BY depth DESC
            """, [node.id])
            rows = cursor.fetchall()

        return '/'.join(row[0] for row in rows)