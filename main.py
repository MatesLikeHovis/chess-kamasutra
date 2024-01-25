import chess, chess.pgn
import requests
import json
import csv
from bs4 import BeautifulSoup

whiteGameList = []
blackGameList = []
positionList = {}


def get_stockfish(board):
    eval = 0
    posRequest = "https://stockfish.online/api/stockfish.php?"
    posRequest += "fen=" + str(board.board_fen())
    posRequest += "%20"
    if board.turn == chess.WHITE:
        posRequest += "w%20"
    else:
        posRequest += 'b%20'
    posCastle = ""
    if board.has_kingside_castling_rights(chess.WHITE):
        posCastle += "K"
    if board.has_queenside_castling_rights(chess.WHITE):
        posCastle += "Q"
    if board.has_kingside_castling_rights(chess.BLACK):
        posCastle += "k"
    if board.has_queenside_castling_rights(chess.BLACK):
        posCastle += "q"
    if posCastle == '':
        posCastle = '-'
    posRequest += posCastle + "%20"
    posEP = ''
    if board.ep_square is None:
        posEP = '-'
    else:
        en_passante_square = chess.square_name(board.ep_square)
    posRequest += posEP + "%200%20"
    posRequest += str(board.fullmove_number)
    posRequest += "&depth=2&mode=eval"
    posResp = requests.get(posRequest)
    try:
        json_content = posResp.content.decode('utf-8')
        content_dict = json.loads(json_content)
        data_value = content_dict.get('data', '')
        total_evaluation_str = data_value.split('Total evaluation: ')[1].split()[0]
        total_evaluation = float(total_evaluation_str)
        eval = total_evaluation
    except: eval = 0
    return eval

def create_game_lists(user):
    pgn = open(user + "Games.pgn")
    finished = False
    while not finished:
        try:
            thisGame = chess.pgn.read_game(pgn)
        except:
            finished = True
        else:
            if thisGame:
                if thisGame.headers['Black'] == user:
                    blackGameList.append(thisGame)
                else:
                    whiteGameList.append(thisGame)
            else:
                finished = True

def download_pgn_file(user):
    userDownload = "https://lichess.org/api/games/user/" + user

    req = requests.get(userDownload, stream=True)
    headers = req.headers
    total_length = 0
    fileName = user + "Games.pgn"

    with open(fileName,'wb') as file:
        print("File located, downloading begun.")
        dl_amount = 0
        for chunk in req.iter_content(chunk_size=128):
            if chunk:
                file.write(chunk)
                dl_amount += len(chunk)
            if dl_amount % 10000 < 100:
                print(str(dl_amount / 1000) + " kb downloaded")

def create_position_list(gameList, chessColor, color, oppcolor):
    counter = 1
    for game in gameList:
        board = game.board()
        opponent = game.headers[oppcolor]
        result = ''
        if game.headers['Result'] == '0-1':
            result = 'L'
        elif game.headers['Result'] == '1-0':
            result = 'W'
        else:
            result = "D"
        print("Generating Position List")
        prev_board_fen = "None"
        for move in game.mainline_moves():
            board.push(move)
            if board.turn == chessColor: 
                thisPosDict = {}
                thisPosDict['Color'] = [color]
                if board.move_stack:
                    try:
                        thisPosDict['Last Move'] = [board.move_stack[-2].uci()]
                    except:
                        thisPosDict['Last Move'] = ['None']
                    try:
                        thisPosDict['Opponent Move'] = [board.move_stack[-1].uci()]
                    except:
                        thisPosDict['Opponent Move'] = ['None']
                else: thisPosDict['Last Move'] = ['None']
                if prev_board_fen != "None":
                    if prev_board_fen in positionList.keys():
                        try:
                            positionList[prev_board_fen][-1]['This Move'] = [board.move_stack[-2].uci()]
                        except:
                            positionList[prev_board_fen][-1]['This Move'] = ['None']
                thisPosDict['Moves Completed'] = [(board.fullmove_number - 1)]
                thisPosDict['Opponent'] = [opponent]
                thisPosDict['Result'] = [result]
        
                # Evaluation has been removed at this point to simplify and speed the process.
                #eval = get_stockfish(board)
                #thisPosDict['Evaluation'] = eval

                if board.board_fen() not in positionList.keys():
                    positionList[board.board_fen()] = [thisPosDict]
                else:
                    positionList[board.board_fen()].append(thisPosDict)
                prev_board_fen = board.board_fen()
        print("Game " + str(counter) + " of " + str(len(gameList)) + " Completed")
        counter += 1


print("Hello Dear User!")
print("Please enter a LiChess user name to begin downloading PGN file.")
user = input(": ")

try:
    filePath = user + "Games.pgn"
    with open(filePath, 'r') as file:
        pass
except:
    download_pgn_file(user)


    
print("Download complete.")
print("Beginning analysis and categorization.")

create_game_lists(user)
create_position_list(whiteGameList, chess.WHITE, 'White', 'Black')
create_position_list(blackGameList, chess.BLACK, 'Black', 'White')

print("Game lists populated")

print("Generating CSV File")
csvPath = user + "Positions.csv"
with open(csvPath, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    if positionList:
        first_position = next(iter(positionList))
        header_dict = positionList[first_position][0]
        csv_writer.writerow(['FEN Position'] + list(header_dict.keys()))
        for position, pos_list in positionList.items():
            for thisPositionDict in pos_list:
                csv_writer.writerow([position] + list(thisPositionDict.values()))
    else: print("Error - no position list")

print("Success!!!")
