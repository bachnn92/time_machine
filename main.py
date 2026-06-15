from src.matrix import generate_commit_matrix, create_8bit_ui

if __name__ == "__main__":
    # Example usage
    plan_name = "data.json"
    year = 2015
    matrix = generate_commit_matrix(year)
    create_8bit_ui(matrix, year)