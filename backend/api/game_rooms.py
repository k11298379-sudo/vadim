import random
import time
import uuid
import logging
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

try:
    import chess
except ImportError:
    chess = None
    logger.warning("Module 'chess' is not installed. Chess games will be unavailable until installed.")

from backend.api.rpg_bosses import RAID_BOSSES
from backend.api.rpg_pvp import RPGPvPRoom
from backend.api.rpg_coop import RPGCoopBossRoom


WIN_COMBOS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Cols
    (0, 4, 8), (2, 4, 6)              # Diags
]

class TicTacToeRoom:
    def __init__(
        self,
        room_id: str,
        host_tg_id: int,
        host_name: str,
        opponent_tg_id: Optional[int] = None,
        opponent_name: Optional[str] = None
    ):
        self.room_id = room_id
        self.game_type = "tictactoe"
        self.host_tg_id = host_tg_id
        self.host_name = host_name
        self.opponent_tg_id = opponent_tg_id
        self.opponent_name = opponent_name or "Соперник"
        
        # State: "waiting", "playing", "finished", "rejected", "canceled"
        self.status = "waiting"
        self.board = [""] * 9
        self.turn = "X"  # Host is X, opponent is O
        self.winner: Optional[str] = None  # "X", "O", "draw", or None
        self.rematch_requested_by: Optional[str] = None  # "X", "O", or None
        
        self.created_at = time.time()
        self.last_activity = time.time()

    def set_opponent(self, user_tg_id: int, user_name: Optional[str] = None):
        self.opponent_tg_id = user_tg_id
        self.o_tg_id = user_tg_id
        if user_name:
            self.opponent_name = user_name
            self.o_name = user_name

    def get_player_role(self, user_tg_id: int) -> Optional[str]:
        if user_tg_id == self.host_tg_id:
            return "X"
        if self.opponent_tg_id and user_tg_id == self.opponent_tg_id:
            return "O"
        return None

    def check_winner(self) -> Optional[str]:
        for a, b, c in WIN_COMBOS:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        if all(cell != "" for cell in self.board):
            return "draw"
        return None

    def make_move(self, user_tg_id: int, cell_idx: Any) -> tuple[bool, str]:
        self.last_activity = time.time()
        if self.status != "playing":
            return False, "Игра не активна"

        role = self.get_player_role(user_tg_id)
        if not role:
            return False, "Вы не участник этой игры"

        if self.turn != role:
            return False, "Сейчас ход другого игрока"

        try:
            c_idx = int(cell_idx)
        except Exception:
            return False, "Неверный индекс клетки"

        if not (0 <= c_idx < 9):
            return False, "Неверный индекс клетки"

        if self.board[c_idx] != "":
            return False, "Клетка уже занята"

        self.board[c_idx] = role
        win = self.check_winner()
        if win:
            self.status = "finished"
            self.winner = win
        else:
            self.turn = "O" if self.turn == "X" else "X"

        return True, "Успешно"

    def request_rematch(self, user_tg_id: int) -> tuple[bool, str]:
        self.last_activity = time.time()
        if self.status != "finished":
            return False, "Игра еще не окончена"

        role = self.get_player_role(user_tg_id)
        if not role:
            return False, "Вы не участник этой игры"

        other_role = "O" if role == "X" else "X"
        if self.rematch_requested_by == other_role:
            # Both agreed to rematch! Reset board
            self.board = [""] * 9
            self.turn = "X"
            self.winner = None
            self.rematch_requested_by = None
            self.status = "playing"
            return True, "Реванш начат"
        else:
            self.rematch_requested_by = role
            return True, "Запрос на реванш отправлен"

    def to_dict(self, viewer_tg_id: Optional[int] = None) -> dict:
        viewer_role = self.get_player_role(viewer_tg_id) if viewer_tg_id else None
        return {
            "room_id": self.room_id,
            "game_type": "tictactoe",
            "status": self.status,
            "host": {
                "tg_id": self.host_tg_id,
                "name": self.host_name,
                "role": "X"
            },
            "opponent": {
                "tg_id": self.opponent_tg_id,
                "name": self.opponent_name,
                "role": "O"
            } if self.opponent_tg_id else None,
            "board": self.board,
            "turn": self.turn,
            "winner": self.winner,
            "rematch_requested_by": self.rematch_requested_by,
            "your_role": viewer_role,
            "is_your_turn": (self.status == "playing" and self.turn == viewer_role)
        }


class ChessRoom:
    def __init__(
        self,
        room_id: str,
        host_tg_id: int,
        host_name: str,
        opponent_tg_id: Optional[int] = None,
        opponent_name: Optional[str] = None,
        host_color: str = "white",
        is_local: bool = False
    ):
        self.room_id = room_id
        self.game_type = "chess"
        self.host_tg_id = host_tg_id
        self.host_name = host_name
        self.opponent_tg_id = opponent_tg_id
        self.opponent_name = opponent_name or "Соперник"
        self.is_local = is_local

        # Randomize host color if requested
        if host_color == "random":
            actual_color = random.choice(["white", "black"])
            self.color_choice_mode = "random"
        else:
            actual_color = host_color if host_color in ["white", "black"] else "white"
            self.color_choice_mode = actual_color

        self.host_color = actual_color

        if self.host_color == "white":
            self.white_tg_id = host_tg_id
            self.white_name = host_name
            self.black_tg_id = opponent_tg_id
            self.black_name = self.opponent_name
        else:
            self.black_tg_id = host_tg_id
            self.black_name = host_name
            self.white_tg_id = opponent_tg_id
            self.white_name = self.opponent_name

        if chess is None:
            raise RuntimeError("Библиотека шахмат chess не установлена на сервере. Обратитесь к администратору.")

        self.board = chess.Board()
        self.status = "playing" if is_local else "waiting"
        self.winner: Optional[str] = None  # "white", "black", "draw", or None
        self.termination_reason: Optional[str] = None  # "checkmate", "stalemate", "resignation", etc.
        self.rematch_requested_by: Optional[str] = None  # "white", "black", or None

        self.created_at = time.time()
        self.last_activity = time.time()

    def set_opponent(self, user_tg_id: int, user_name: Optional[str] = None):
        self.opponent_tg_id = user_tg_id
        if user_name:
            self.opponent_name = user_name
        if self.host_color == "white":
            self.black_tg_id = user_tg_id
            if user_name:
                self.black_name = user_name
        else:
            self.white_tg_id = user_tg_id
            if user_name:
                self.white_name = user_name

    def get_player_role(self, user_tg_id: int) -> Optional[str]:
        if getattr(self, "is_local", False):
            return self.turn
        if self.white_tg_id and user_tg_id == self.white_tg_id:
            return "white"
        if self.black_tg_id and user_tg_id == self.black_tg_id:
            return "black"
        return None

    @property
    def turn(self) -> str:
        return "white" if self.board.turn == chess.WHITE else "black"

    def make_move(self, user_tg_id: int, move_data: Any) -> tuple[bool, str]:
        self.last_activity = time.time()
        if self.status != "playing":
            return False, "Игра не активна"

        if not getattr(self, "is_local", False):
            role = self.get_player_role(user_tg_id)
            if not role:
                return False, "Вы не участник этой игры"

            if self.turn != role:
                return False, "Сейчас ход другого игрока"

        uci_str = str(move_data).strip().lower()
        try:
            move = chess.Move.from_uci(uci_str)
        except Exception:
            return False, f"Некорректный формат хода: {uci_str}"

        if move not in self.board.legal_moves:
            # Check if auto-promotion to queen works
            if len(uci_str) == 4:
                try_promo = chess.Move.from_uci(uci_str + "q")
                if try_promo in self.board.legal_moves:
                    move = try_promo
                else:
                    return False, "Недопустимый ход по правилам шахмат"
            else:
                return False, "Недопустимый ход по правилам шахмат"

        self.board.push(move)

        # Check outcome
        if self.board.is_checkmate():
            self.status = "finished"
            self.winner = "white" if self.board.turn == chess.BLACK else "black"
            self.termination_reason = "checkmate"
        elif self.board.is_stalemate():
            self.status = "finished"
            self.winner = "draw"
            self.termination_reason = "stalemate"
        elif self.board.is_insufficient_material():
            self.status = "finished"
            self.winner = "draw"
            self.termination_reason = "insufficient_material"
        elif self.board.can_claim_threefold_repetition():
            self.status = "finished"
            self.winner = "draw"
            self.termination_reason = "repetition"
        elif self.board.can_claim_fifty_moves():
            self.status = "finished"
            self.winner = "draw"
            self.termination_reason = "fifty_moves"

        return True, "Успешно"

    def resign(self, user_tg_id: int) -> tuple[bool, str]:
        self.last_activity = time.time()
        if self.status != "playing":
            return False, "Игра не активна"

        if getattr(self, "is_local", False):
            role = self.turn
            self.status = "finished"
            self.winner = "black" if role == "white" else "white"
            self.termination_reason = "resignation"
            return True, "Сдача принята"

        role = self.get_player_role(user_tg_id)
        if not role:
            return False, "Вы не участник этой игры"

        self.status = "finished"
        self.winner = "black" if role == "white" else "white"
        self.termination_reason = "resignation"
        return True, "Сдача принята"

    def request_rematch(self, user_tg_id: int) -> tuple[bool, str]:
        self.last_activity = time.time()
        if self.status != "finished":
            return False, "Игра еще не окончена"

        if getattr(self, "is_local", False):
            self.board.reset()
            self.winner = None
            self.termination_reason = None
            self.rematch_requested_by = None
            self.status = "playing"
            return True, "Новая игра начата"

        role = self.get_player_role(user_tg_id)
        if not role:
            return False, "Вы не участник этой игры"

        other_role = "black" if role == "white" else "white"
        if self.rematch_requested_by == other_role:
            # Both agreed: swap colors and restart!
            self.white_tg_id, self.black_tg_id = self.black_tg_id, self.white_tg_id
            self.white_name, self.black_name = self.black_name, self.white_name
            self.host_color = "black" if self.host_color == "white" else "white"

            self.board.reset()
            self.winner = None
            self.termination_reason = None
            self.rematch_requested_by = None
            self.status = "playing"
            return True, "Реванш начат со сменой цветов"
        else:
            self.rematch_requested_by = role
            return True, "Запрос на реванш отправлен"

    def get_captured_pieces(self) -> dict:
        initial = {
            "white": {"P": 8, "N": 2, "B": 2, "R": 2, "Q": 1},
            "black": {"p": 8, "n": 2, "b": 2, "r": 2, "q": 1}
        }
        current_counts: Dict[str, int] = {}
        for piece in self.board.piece_map().values():
            sym = piece.symbol()
            current_counts[sym] = current_counts.get(sym, 0) + 1

        captured_by_white = []
        for sym, count in initial["black"].items():
            diff = count - current_counts.get(sym, 0)
            if diff > 0:
                captured_by_white.extend([sym] * diff)

        captured_by_black = []
        for sym, count in initial["white"].items():
            diff = count - current_counts.get(sym, 0)
            if diff > 0:
                captured_by_black.extend([sym] * diff)

        return {
            "by_white": captured_by_white,
            "by_black": captured_by_black
        }

    def to_dict(self, viewer_tg_id: Optional[int] = None) -> dict:
        is_local = getattr(self, "is_local", False)
        viewer_role = self.turn if is_local else (self.get_player_role(viewer_tg_id) if viewer_tg_id else None)
        last_move = self.board.peek().uci() if len(self.board.move_stack) > 0 else None
        legal_moves = [m.uci() for m in self.board.legal_moves] if self.status == "playing" else []

        host_role = "white" if is_local else self.get_player_role(self.host_tg_id)
        opp_role = "black" if is_local else (self.get_player_role(self.opponent_tg_id) if self.opponent_tg_id else None)

        return {
            "room_id": self.room_id,
            "game_type": "chess",
            "is_local": is_local,
            "status": self.status,
            "host_color": self.host_color,
            "color_choice_mode": getattr(self, "color_choice_mode", self.host_color),
            "host": {
                "tg_id": self.host_tg_id,
                "name": self.host_name,
                "role": host_role
            },
            "opponent": {
                "tg_id": self.opponent_tg_id,
                "name": self.opponent_name,
                "role": opp_role
            } if self.opponent_tg_id else None,
            "white": {
                "tg_id": self.white_tg_id,
                "name": self.white_name
            },
            "black": {
                "tg_id": self.black_tg_id,
                "name": self.black_name
            } if self.black_tg_id else None,
            "fen": self.board.fen(),
            "turn": self.turn,
            "winner": self.winner,
            "termination_reason": self.termination_reason,
            "rematch_requested_by": self.rematch_requested_by,
            "your_role": viewer_role,
            "is_your_turn": (self.status == "playing") if is_local else (self.status == "playing" and self.turn == viewer_role),
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "last_move": last_move,
            "legal_moves": legal_moves,
            "captured_pieces": self.get_captured_pieces()
        }


class GameRoomManager:
    def __init__(self):
        self.rooms: Dict[str, Any] = {}

    def cleanup(self):
        now = time.time()
        expired = [rid for rid, r in self.rooms.items() if now - r.last_activity > 7200]
        for rid in expired:
            del self.rooms[rid]

    def create_local_room(
        self,
        host_tg_id: int,
        host_name: str,
        game_type: str = "chess"
    ) -> Any:
        self.cleanup()
        room_id = "local_" + uuid.uuid4().hex[:8]
        if game_type == "chess":
            room = ChessRoom(
                room_id=room_id,
                host_tg_id=host_tg_id,
                host_name=host_name or "Белые",
                opponent_tg_id=host_tg_id,
                opponent_name="Черные",
                host_color="white",
                is_local=True
            )
            self.rooms[room_id] = room
            return room
        raise ValueError(f"Локальный режим не поддерживается для {game_type}")

    def create_room(
        self,
        host_tg_id: int,
        host_name: str,
        opponent_tg_id: Optional[int] = None,
        opponent_name: Optional[str] = None,
        game_type: str = "tictactoe",
        host_color: str = "white",
        boss_id: str = "roshan",
        is_solo: bool = False,
        hero_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        self.cleanup()
        room_id = uuid.uuid4().hex[:10]
        if game_type == "chess":
            room = ChessRoom(
                room_id=room_id,
                host_tg_id=host_tg_id,
                host_name=host_name,
                opponent_tg_id=opponent_tg_id,
                opponent_name=opponent_name,
                host_color=host_color
            )
        elif game_type == "rpg_duel":
            from backend.api.rpg_pvp import RPGPvPRoom
            room = RPGPvPRoom(
                room_id=room_id,
                host_tg_id=host_tg_id,
                host_name=host_name,
                opponent_tg_id=opponent_tg_id,
                opponent_name=opponent_name,
                hero_data=hero_data
            )
        elif game_type == "rpg_coop":
            from backend.api.rpg_coop import RPGCoopBossRoom
            room = RPGCoopBossRoom(
                room_id=room_id,
                host_tg_id=host_tg_id,
                host_name=host_name,
                opponent_tg_id=opponent_tg_id,
                opponent_name=opponent_name,
                boss_id=boss_id,
                is_solo=is_solo,
                hero_data=hero_data
            )
        else:
            room = TicTacToeRoom(
                room_id=room_id,
                host_tg_id=host_tg_id,
                host_name=host_name,
                opponent_tg_id=opponent_tg_id,
                opponent_name=opponent_name
            )
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[Any]:
        return self.rooms.get(room_id)

    def join_room(self, room_id: str, user_tg_id: int, user_name: str) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Комната не найдена"

        if room.status in ["canceled", "rejected"]:
            return False, f"Игра была отменена ({room.status})"

        if user_tg_id == room.host_tg_id:
            return True, "Вы создатель комнаты"

        if hasattr(room, "add_coop_player"):
            return room.add_coop_player(user_tg_id, user_name)

        if room.opponent_tg_id and room.opponent_tg_id != user_tg_id:
            return False, "Эта игра предназначена для другого игрока"

        # Opponent joins
        if hasattr(room, "set_opponent"):
            room.set_opponent(user_tg_id, user_name)
        else:
            room.opponent_tg_id = user_tg_id
            if user_name:
                room.opponent_name = user_name

        if room.status == "waiting":
            room.status = "playing"
        room.last_activity = time.time()
        return True, "Успешное подключение"

    def add_bot_to_coop(self, room_id: str) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room or getattr(room, "game_type", None) != "rpg_coop":
            return False, "Комната рейда не найдена"
        if hasattr(room, "add_bot_ally"):
            return room.add_bot_ally()
        return False, "Не поддерживается"

    def make_move(self, room_id: str, user_tg_id: int, move_data: Any) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Комната не найдена"
        return room.make_move(user_tg_id, move_data)

    def resign_room(self, room_id: str, user_tg_id: int) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Комната не найдена"
        if hasattr(room, "resign"):
            return room.resign(user_tg_id)
        return False, "Сдача не поддерживается в этой игре"

    def request_rematch(self, room_id: str, user_tg_id: int) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Комната не найдена"
        return room.request_rematch(user_tg_id)

    def reject_room(self, room_id: str, user_tg_id: int) -> bool:
        room = self.get_room(room_id)
        if not room:
            return False
        if room.opponent_tg_id and room.opponent_tg_id != user_tg_id:
            return False
        room.status = "rejected"
        room.last_activity = time.time()
        return True

    def cancel_room(self, room_id: str, user_tg_id: int) -> bool:
        room = self.get_room(room_id)
        if not room:
            return False
        if room.host_tg_id != user_tg_id:
            return False
        room.status = "canceled"
        room.last_activity = time.time()
        return True


# Global game room manager instance
game_manager = GameRoomManager()
