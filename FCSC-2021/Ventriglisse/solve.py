import base64
from io import BytesIO

import networkx
from PIL import Image
from pwn import *

CASE_SIZE = 64


class Case:
    def __init__(self, top, right, bottom, left, start, end):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left
        self.start = start
        self.end = end

    def __str__(self):
        return f'T: {self.top}  B: {self.bottom}\n' \
               f'L: {self.left}  R: {self.right}\n' \
               f'S: {self.start}  E: {self.end}'


def find_path(img):
    graph = networkx.DiGraph()

    max_x = (img.width // 64) - 1
    max_y = (img.height // 64) - 1

    # Parse maze
    maze = []
    for y in range(2, max_y):
        maze.append([])
        for x in range(1, max_x):
            case_x = x * CASE_SIZE
            case_y = y * CASE_SIZE
            # Find case walls
            wall_top = img.getpixel((case_x + 10, case_y)) == (0, 0, 255)
            wall_right = img.getpixel((case_x + CASE_SIZE - 1, case_y + 10)) == (0, 0, 255)
            wall_bottom = img.getpixel((case_x + 10, case_y + CASE_SIZE - 1)) == (0, 0, 255)
            wall_left = img.getpixel((case_x, case_y + 10)) == (0, 0, 255)
            # Is it a start or end case?
            start = img.getpixel((case_x + 30, case_y + CASE_SIZE + 25)) == (229, 20, 0)
            end = img.getpixel((case_x + 30, case_y - 15)) == (229, 20, 0)
            # Memorize the case
            case = Case(wall_top, wall_right, wall_bottom, wall_left, start, end)
            maze[y-2].append(case)

    # Transform the maze to a graph
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            case = maze[y][x]

            if case.top or case.right or case.bottom or case.left:
                # Top to bottom
                for slide_y in range(y, len(maze)):
                    slide_case = maze[slide_y][x]
                    if slide_case.bottom:
                        break
                if case != slide_case:
                    graph.add_edge((x, y), (x, slide_y))
                # Right to left
                for slide_x in range(x, -1, -1):
                    slide_case = maze[y][slide_x]
                    if slide_case.left:
                        break
                if case != slide_case:
                    graph.add_edge((x, y), (slide_x, y))
                # Bottom to top
                for slide_y in range(y, -1, -1):
                    slide_case = maze[slide_y][x]
                    if slide_case.top:
                        break
                if case != slide_case:
                    graph.add_edge((x, y), (x, slide_y))
                if case.start:
                    graph.add_edge('start', (x, slide_y))
                # Left to right
                for slide_x in range(x, len(maze[0])):
                    slide_case = maze[y][slide_x]
                    if slide_case.right:
                        break
                if case != slide_case:
                    graph.add_edge((x, y), (slide_x, y))

            if case.end:
                graph.add_edge((x, y), 'end')

    # Find shortest path
    path = networkx.shortest_path(graph, 'start', 'end')

    path_str = 'N'
    for i in range(1, len(path) - 2):
        x1, y1 = path[i]
        x2, y2 = path[i+1]
        if y1 < y2:
            path_str += 'S'
        if y1 > y2:
            path_str += 'N'
        if x1 < x2:
            path_str += 'E'
        if x1 > x2:
            path_str += 'O'

    if path_str[-1] != 'N':
        path_str += 'N'

    return path_str


r = remote('challenges1.france-cybersecurity-challenge.fr', 7002, level='debug')
r.recvuntil('ready...')
r.sendline()

while True:
    raw = r.recvuntil('END MAZE').decode()
    raw_b64 = ''.join(raw.split('BEGIN MAZE')[1].splitlines()[1:-1])
    img = Image.open(BytesIO(base64.b64decode(raw_b64)))

    try:
        r.sendline(find_path(img))
    except networkx.exception.NodeNotFound:
        img.save('ohno.png')
        raise
