import aiosql
import aiosqlite
import asyncio
from pathlib import Path

class Database:
    def __init__(self, db_path="game.db"):
        self.db_path = db_path
        self.queries = None
        
    async def initialize(self):
        sql_dir = Path(__file__).parent / "sql"
        
        # Load SQL queries
        self.queries = aiosql.from_path(sql_dir / "queries.sql", "aiosqlite")
        
        # Create database and tables
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Read and execute schema
            schema_path = sql_dir / "schema.sql"
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            await db.executescript(schema)
            await db.commit()
            
        # Insert some basic items for testing
        await self._create_basic_items()
            
    async def get_connection(self):
        conn = await aiosqlite.connect(
            self.db_path,
            timeout=30.0,  # 30 second timeout
            isolation_level=None  # Autocommit mode
        )
        conn.row_factory = aiosqlite.Row  # This makes rows work like dictionaries
        
        # Configure SQLite for better concurrency
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL") 
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=memory")
        
        return conn
    
    class connection:
        def __init__(self, database):
            self.database = database
            self.conn = None
            
        async def __aenter__(self):
            self.conn = await self.database.get_connection()
            return self.conn
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.conn:
                await self.conn.close()
    
    def get_connection_context(self):
        return self.connection(self)
    
    async def execute_query(self, query_name, *args, **kwargs):
        """Execute a query and return results"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            query_func = getattr(self.queries, query_name)
            result = await query_func(conn, *args, **kwargs)
            return result
    
    async def execute_query_with_commit(self, query_name, *args, **kwargs):
        """Execute a query that modifies data and commit"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            query_func = getattr(self.queries, query_name)
            result = await query_func(conn, *args, **kwargs)
            await conn.commit()
            return result
        
    async def _create_basic_items(self):
        """Create some basic starter items"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Basic weapons
            await db.execute("""
                INSERT OR IGNORE INTO items (name, slot_id, rarity_id, level_requirement, attack, hit_points, description)
                VALUES 
                ('Rusty Sword', 5, 1, 1, 15, 0, 'A basic starting weapon'),
                ('Iron Sword', 5, 2, 5, 35, 5, 'A decent iron weapon'),
                ('Steel Blade', 5, 3, 15, 85, 15, 'A fine steel weapon'),
                ('Plasma Rifle', 5, 4, 30, 250, 50, 'High-tech energy weapon'),
                ('Chaos Destroyer', 5, 5, 60, 750, 150, 'Legendary weapon of destruction')
            """)
            
            # Basic armor
            await db.execute("""
                INSERT OR IGNORE INTO items (name, slot_id, rarity_id, level_requirement, attack, hit_points, description)
                VALUES 
                ('Cloth Shirt', 2, 1, 1, 0, 25, 'Basic cloth armor'),
                ('Leather Vest', 2, 2, 5, 0, 65, 'Sturdy leather protection'),
                ('Chain Mail', 2, 3, 15, 0, 155, 'Metal chain protection'),
                ('Power Armor', 2, 4, 30, 0, 400, 'Advanced protective suit'),
                ('Mythic Robes', 2, 5, 60, 50, 1200, 'Legendary magical armor')
            """)
            
            # Basic helmets
            await db.execute("""
                INSERT OR IGNORE INTO items (name, slot_id, rarity_id, level_requirement, attack, hit_points, fire_resist, description)
                VALUES 
                ('Cloth Cap', 1, 1, 1, 0, 15, 5, 'Basic head protection'),
                ('Leather Helm', 1, 2, 5, 0, 35, 15, 'Sturdy leather helmet'),
                ('Steel Helmet', 1, 3, 15, 0, 85, 35, 'Strong metal helmet'),
                ('Combat Visor', 1, 4, 30, 0, 220, 85, 'High-tech protective visor'),
                ('Crown of Power', 1, 5, 60, 25, 650, 250, 'Legendary royal crown')
            """)
            
            # Basic accessories
            await db.execute("""
                INSERT OR IGNORE INTO items (name, slot_id, rarity_id, level_requirement, rage_per_hour, experience_per_hour, gold_per_turn, description)
                VALUES 
                ('Simple Amulet', 7, 1, 1, 10, 5, 1, 'Basic magical amulet'),
                ('Energy Crystal', 7, 2, 10, 25, 15, 3, 'Glowing energy source'),
                ('Power Core', 7, 3, 25, 65, 35, 8, 'Advanced energy core'),
                ('Quantum Device', 7, 4, 40, 150, 85, 20, 'Quantum technology'),
                ('Infinity Stone', 7, 5, 70, 500, 250, 75, 'Legendary cosmic artifact')
            """)
            
            await db.commit()

# Global database instance
db = Database()

async def init_database():
    await db.initialize()
    
async def get_db():
    return db