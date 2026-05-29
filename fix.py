f = open('src/infrastructure/database/repositories_impl.py', 'r', encoding='utf-8')
c = f.read()
f.close()
c = c.replace(
    "    def evento_existe(self, event_id: str) -> bool:
        from src.infrastructure.database.models import EventoModel
        return self._db.query(EventoModel).filter(EventoModel.event_id == event_id, EventoModel.status == 'processed').first() is not None",
    "    def evento_existe(self, event_id: str) -> bool:\n        from src.infrastructure.database.models import EventoModel\n        return self._db.query(EventoModel).filter(EventoModel.event_id == event_id, EventoModel.status == 'processed').first() is not None"
)
f = open('src/infrastructure/database/repositories_impl.py', 'w', encoding='utf-8')
f.write(c)
f.close()
print('done')
