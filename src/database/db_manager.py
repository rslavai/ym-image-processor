"""
Database Manager for K+ Content Service V2.0
Handles migrations, seeding, and database connections
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class DatabaseManager:
    """Manages database operations, migrations, and seeding"""
    
    def __init__(self, db_path: str = "database/history.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_dir = Path(self.db_path).parent
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.seeds_dir = Path(__file__).parent / "seeds"
        
        # Ensure database directory exists
        self.db_dir.mkdir(exist_ok=True)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with JSON support"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def run_migrations(self) -> bool:
        """
        Run all pending migrations
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            
            # Create migrations tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get executed migrations
            executed = {row[0] for row in conn.execute("SELECT filename FROM migrations")}
            
            # Run pending migrations in order
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                if migration_file.name not in executed:
                    print(f"🔄 Running migration: {migration_file.name}")
                    
                    # Read and execute migration
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                    
                    # Execute migration (may contain multiple statements)
                    conn.executescript(migration_sql)
                    
                    # Record as executed
                    conn.execute(
                        "INSERT INTO migrations (filename) VALUES (?)",
                        (migration_file.name,)
                    )
                    
                    print(f"✅ Migration completed: {migration_file.name}")
            
            conn.commit()
            conn.close()
            
            print("✅ All migrations completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def run_seeds(self, force: bool = False) -> bool:
        """
        Run seed data
        
        Args:
            force: If True, run seeds even if already executed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            
            # Create seeds tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get executed seeds
            executed = {row[0] for row in conn.execute("SELECT filename FROM seeds")}
            
            # Run pending seeds in order
            seed_files = sorted(self.seeds_dir.glob("*.sql"))
            
            for seed_file in seed_files:
                if force or seed_file.name not in executed:
                    print(f"🌱 Running seed: {seed_file.name}")
                    
                    # Read and execute seed
                    with open(seed_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                    
                    # Execute seed
                    conn.executescript(seed_sql)
                    
                    # Record as executed (use INSERT OR REPLACE for force mode)
                    if force:
                        conn.execute(
                            "INSERT OR REPLACE INTO seeds (filename) VALUES (?)",
                            (seed_file.name,)
                        )
                    else:
                        conn.execute(
                            "INSERT INTO seeds (filename) VALUES (?)",
                            (seed_file.name,)
                        )
                    
                    print(f"✅ Seed completed: {seed_file.name}")
            
            conn.commit()
            conn.close()
            
            print("✅ All seeds completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def initialize_database(self, force_seeds: bool = False) -> bool:
        """
        Initialize database with migrations and seeds
        
        Args:
            force_seeds: If True, re-run seeds even if already executed
            
        Returns:
            True if successful, False otherwise
        """
        print("🔧 Initializing database...")
        
        # Run migrations first
        if not self.run_migrations():
            return False
        
        # Then run seeds
        if not self.run_seeds(force=force_seeds):
            return False
        
        print("🎉 Database initialization completed!")
        return True
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            conn = self.get_connection()
            
            # Get tables
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()
            
            schema_info = {
                'tables': [],
                'migrations_executed': [],
                'seeds_executed': []
            }
            
            # Get table info
            for table in tables:
                table_name = table[0]
                columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                
                schema_info['tables'].append({
                    'name': table_name,
                    'columns': [dict(col) for col in columns]
                })
            
            # Get migration history
            try:
                migrations = conn.execute(
                    "SELECT filename, executed_at FROM migrations ORDER BY executed_at"
                ).fetchall()
                schema_info['migrations_executed'] = [dict(m) for m in migrations]
            except sqlite3.OperationalError:
                pass  # migrations table doesn't exist yet
            
            # Get seed history
            try:
                seeds = conn.execute(
                    "SELECT filename, executed_at FROM seeds ORDER BY executed_at"
                ).fetchall()
                schema_info['seeds_executed'] = [dict(s) for s in seeds]
            except sqlite3.OperationalError:
                pass  # seeds table doesn't exist yet
            
            conn.close()
            return schema_info
            
        except Exception as e:
            print(f"❌ Failed to get schema info: {e}")
            return {}


# Global database manager instance
db_manager = DatabaseManager()


def init_database(force_seeds: bool = False) -> bool:
    """Convenience function to initialize database"""
    return db_manager.initialize_database(force_seeds=force_seeds)