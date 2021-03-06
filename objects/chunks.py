import abc
import io
import json

import lz4.frame
from PIL import Image

from utils import colors
from utils.lzstring import LZString


class Chunky(abc.ABC):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._image = None

    @property
    @abc.abstractmethod
    def height(self): pass

    @property
    def image(self):
        return self._image

    @property
    @abc.abstractmethod
    def p_x(self): pass

    @property
    @abc.abstractmethod
    def p_y(self): pass

    @property
    @abc.abstractmethod
    def url(self): pass

    @abc.abstractmethod
    def is_in_bounds(self): pass

    @abc.abstractmethod
    def load(self, data): pass

    @staticmethod
    @abc.abstractmethod
    def get_intersecting(x, y, dx, dy): pass

    @property
    @abc.abstractmethod
    def width(self): pass

    def __eq__(self, other):
        if type(other) is BigChunk or type(other is ChunkPz):
            return self.y == other.y and self.x == other.x
        return False

    def __hash__(self):
        return hash((self.x, self.y))


class BigChunk(Chunky):
    palette = [x for sub in colors.pixelcanvas for x in sub] * 16

    @property
    def height(self):
        return 960

    @property
    def p_x(self):
        return self.x * 960 - 448

    @property
    def p_y(self):
        return self.y * 960 - 448

    @property
    def url(self):
        return "https://pixelcanvas.io/api/bigchunk/{0}.{1}.bmp".format(self.x * 15, self.y * 15)

    @property
    def width(self):
        return 960

    def is_in_bounds(self):
        return -1043 <= self.x < 1043 and -1043 <= self.y < 1043

    def load(self, data):
        with io.BytesIO(data) as bio:
            self._image = Image.new("RGB", (960, 960), colors.pixelcanvas[1])
            bio.seek(0)
            for cy in range(0, 960, 64):
                for cx in range(0, 960, 64):
                    if not -1000000 <= self.p_x + cx < 1000000 or not -1000000 <= self.p_y + cy < 1000000:
                        bio.seek(2048, 1)
                        continue
                    img = Image.frombuffer('P', (64, 64), bio.read(2048), 'raw', 'P;4')
                    img.putpalette(self.palette)
                    self._image.paste(img, (cx, cy, cx + 64, cy + 64))

    @staticmethod
    def get_intersecting(x, y, dx, dy):
        bigchunks = []
        dx = (x + dx + 448) // 960
        dy = (y + dy + 448) // 960
        x = (x + 448) // 960
        y = (y + 448) // 960
        for iy in range(y, dy + 1):
            for ix in range(x, dx + 1):
                bigchunks.append(BigChunk(ix, iy))
        return bigchunks, (dx - x + 1, dy - y + 1)


class ChunkPz(Chunky):
    palette = [x for sub in colors.pixelzone for x in sub] * 16

    @property
    def height(self):
        return 512

    @property
    def p_x(self):
        return self.x * 512 - 4096

    @property
    def p_y(self):
        return self.y * 512 - 4096

    @property
    def url(self):
        return "42[\"r\", {{\"cx\": {0}, \"cy\": {1}}}]".format(self.x, self.y)

    @property
    def width(self):
        return 512

    def is_in_bounds(self):
        return 0 <= self.x < 16 and 0 <= self.y < 16

    def load(self, data):
        tmp = LZString().decompressFromBase64(data)
        tmp = json.loads("[" + tmp + "]")
        tmp = lz4.frame.decompress(bytes(tmp))
        self._image = Image.frombytes('P', (512, 512), tmp, 'raw', 'P;4')
        self._image.putpalette(self.palette)

    @staticmethod
    def get_intersecting(x, y, dx, dy):
        x += 4096
        y += 4096
        chunks = []
        dx = (x + dx) // 512
        dy = (y + dy) // 512
        x = x // 512
        y = y // 512
        for iy in range(y, dy + 1):
            for ix in range(x, dx + 1):
                chunks.append(ChunkPz(ix, iy))
        return chunks, (dx - x + 1, dy - y + 1)


class PxlsBoard(Chunky):
    palette = [x for sub in colors.pxlsspace for x in sub]

    def __init__(self):
        super().__init__(0, 0)
        self._info = None

    @property
    def height(self):
        return self._info['height']

    @property
    def p_x(self):
        return 0

    @property
    def p_y(self):
        return 0

    @property
    def url(self):
        return None

    @property
    def width(self):
        return self._info['width']

    def is_in_bounds(self):
        return True

    def load(self, data):
        self._image = Image.frombytes("P", (self._info['width'], self._info['height']), data, 'raw', 'P', 0, 1)
        self._image.putpalette(self.palette)

    def set_board_info(self, info):
        self._info = info

    @staticmethod
    def get_intersecting(x, y, dx, dy):
        return [PxlsBoard()], (1, 1)


class BigChunkPP(BigChunk):
    palette = [x for sub in colors.pixelplace for x in sub] * 16

    @property
    def url(self):
        return "https://pixelplace.fun/api/bigchunk/{0}.{1}.bmp".format(self.x * 15, self.y * 15)

    @staticmethod
    def get_intersecting(x, y, dx, dy):
        bigchunks = []
        dx = (x + dx + 448) // 960
        dy = (y + dy + 448) // 960
        x = (x + 448) // 960
        y = (y + 448) // 960
        for iy in range(y, dy + 1):
            for ix in range(x, dx + 1):
                bigchunks.append(BigChunkPP(ix, iy))
        return bigchunks, (dx - x + 1, dy - y + 1)
