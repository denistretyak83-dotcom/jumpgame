# DIP-схема зависимостей (Direction Inversion Principle)

Цель: зафиксировать, кто от кого зависит, чтобы данные/знания шли
только в нужную сторону (модель не знает про view и наоборот).

## Правила (контракт проекта)
1. Модель (models/*) НЕ знает о pygame в return-значениях.
   view не читает модель напрямую — только через ModelVisualData (DTO).
2. Controller ЕДИНСТВЕННЫЙ читает ввод и переводит в PlayerIntent/события.
3. View зависит от DTO (ModelVisualData), а не от модели.
4. models зависят от core через абстракции (Protocol/интерфейсы),
   не от конкретных классов (DIP).
5. levels зависят от core через entity_factories (WorldFactory, DIP).
6. audio реагирует на события EventBus (из core.event_bus), не знает про модели.
7. Game — оркестратор, использует сервисы (CollisionDirector, LevelFlow,
   LifeManager, ScoreManager) и НЕ содержит игровую логику напрямую.

## Текущая фактическая схема (после Фазы 3)
- Game --use--> CollisionDirector (core/gameplay.py)
- Game --use--> LevelFlow (core/level_flow.py)
- Game --use--> LifeManager, ScoreManager, RespawnService (core/game_services.py)
- CollisionDirector --use--> CollisionSystem (models/collision_system.py)
- CollisionDirector --use--> ScoreManager, EventBus, sounds (DI)
- LevelFlow --use--> LevelManager (levels), WorldFactory (models), Renderer.set_platforms
- Entities (models) --use--> PhysicsEngine (Protocol) + DeathBehavior/RespawnBehavior (Protocol)
- Player --emit--> EventBus (GameEvents.*)
- View (views/*) --read--> ModelVisualData (DTO) от моделей
- Controller (controllers/*) --input--> PlayerIntent

## Поток зависимости (DIP-сокращение)
  init (main.py)
    -> Game (сборка через DI)
    -> CollisionDirector / LevelFlow / Services (сервисные слои)
    -> Protocols / Models (entity, physics, behaviors)
    -> View (через DTO, никогда модель->view напрямую)
  EventBus --повышает слабую связанность--> audio, logger, Game

## Что запрещено
- Импортировать models/.. в views/.. и наоборот напрямую (кроме DTO).
- Использовать pygame в return-значениях моделей (только ModelVisualData).
- Глобalы/Синглтоны для settings/logger (DI через конструкторы).
- Взаимные/циклические импорты между слоями.