from django.db import migrations


class Migration(migrations.Migration):
    """
    Align an already-created `users_usuario` schema to the English model
    name (User) and Spanish snake_case table name (`usuarios`).

    0001 was edited to create User/`usuarios` for new environments; this
    migration only renames leftover physical tables and content types.
    """

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Main table (created by old 0001 as users_usuario)
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios'
                    ) THEN
                        ALTER TABLE users_usuario RENAME TO usuarios;
                    END IF;
                END $$;
                """,
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario_groups'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios_groups'
                    ) THEN
                        ALTER TABLE users_usuario_groups RENAME TO usuarios_groups;
                    END IF;
                END $$;
                """,
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario_user_permissions'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios_user_permissions'
                    ) THEN
                        ALTER TABLE users_usuario_user_permissions
                            RENAME TO usuarios_user_permissions;
                    END IF;
                END $$;
                """,
                """
                UPDATE django_content_type
                SET model = 'user'
                WHERE app_label = 'users' AND model = 'usuario';
                """,
            ],
            reverse_sql=[
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario'
                    ) THEN
                        ALTER TABLE usuarios RENAME TO users_usuario;
                    END IF;
                END $$;
                """,
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios_groups'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario_groups'
                    ) THEN
                        ALTER TABLE usuarios_groups RENAME TO users_usuario_groups;
                    END IF;
                END $$;
                """,
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'usuarios_user_permissions'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'users_usuario_user_permissions'
                    ) THEN
                        ALTER TABLE usuarios_user_permissions
                            RENAME TO users_usuario_user_permissions;
                    END IF;
                END $$;
                """,
                """
                UPDATE django_content_type
                SET model = 'usuario'
                WHERE app_label = 'users' AND model = 'user';
                """,
            ],
        ),
    ]
