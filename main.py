import argparse
import json
import sys

from challenges.easy import solve_easy
from challenges.hard import solve_hard
from challenges.extreme import solve_extreme

LEVELS = {
    "easy": solve_easy,
    "hard": solve_hard,
    "extreme": solve_extreme,
}


def print_result(title: str, result: dict, elapsed: float) -> None:
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  NÍVEL: {title.upper()}")
    print(f"  Tempo: {elapsed:.4f}s")
    print(separator)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def run_level(name: str) -> None:
    fn = LEVELS[name]
    print(f"\n[*] Iniciando nível {name.upper()}...")
    try:
        result, elapsed = fn()
        print_result(name, result, elapsed)
    except Exception as exc:
        print(f"\n[ERRO] Nível {name.upper()} falhou: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="RPA Challenge Bot")
    parser.add_argument(
        "--level",
        choices=list(LEVELS.keys()),
        default=None,
        help="Nível a executar (padrão: todos)",
    )
    args = parser.parse_args()

    if args.level:
        run_level(args.level)
    else:
        for name in LEVELS:
            run_level(name)

    print("\n[✓] Execução concluída.")


if __name__ == "__main__":
    main()