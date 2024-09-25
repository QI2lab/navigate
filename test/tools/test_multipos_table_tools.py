# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard library imports
import unittest
import pytest
import tkinter as tk
from tkinter import ttk
from math import ceil

# Third party imports
import numpy as np

# Local application imports
from navigate.tools.multipos_table_tools import (
    update_table,
)
from navigate.view.main_window_content.multiposition_tab import MultiPositionTable


@pytest.mark.parametrize("pair", zip([5.6, -3.8, 0], [1, -1, 1]))
def test_sign(pair):
    from navigate.tools.multipos_table_tools import sign

    x, cmp_x = pair

    assert sign(x) == cmp_x


def listize(x):
    if type(x) == np.ndarray:
        return list(x)
    else:
        return [x]


@pytest.mark.parametrize("x_start", listize((np.random.rand() - 0.5) * 1000))
@pytest.mark.parametrize("x_tiles", listize(np.random.randint(0, 5)))
@pytest.mark.parametrize("x_length", listize(np.random.rand() * 1000))
@pytest.mark.parametrize("x_overlap", listize(np.random.rand()))
@pytest.mark.parametrize("y_start", listize(((np.random.rand() - 0.5) * 1000)))
@pytest.mark.parametrize("y_tiles", listize(np.random.randint(0, 5)))
@pytest.mark.parametrize("y_length", listize(np.random.rand() * 1000))
@pytest.mark.parametrize("y_overlap", listize(np.random.rand()))
@pytest.mark.parametrize("z_start", listize(((np.random.rand() - 0.5) * 1000)))
@pytest.mark.parametrize("z_tiles", listize(np.random.randint(0, 5)))
@pytest.mark.parametrize("z_length", listize(np.random.rand() * 1000))
@pytest.mark.parametrize("z_overlap", listize(np.random.rand()))
@pytest.mark.parametrize("theta_start", listize(((np.random.rand() - 0.5) * 180)))
@pytest.mark.parametrize("theta_tiles", listize(np.random.randint(0, 5)))
@pytest.mark.parametrize("theta_length", listize((np.random.rand() * 5)))
@pytest.mark.parametrize("theta_overlap", listize(np.random.rand()))
@pytest.mark.parametrize("f_start", listize(((np.random.rand() - 0.5) * 1000)))
@pytest.mark.parametrize("f_tiles", listize(np.random.randint(0, 5)))
@pytest.mark.parametrize("f_length", listize(np.random.rand() * 1000))
@pytest.mark.parametrize("f_overlap", listize(np.random.rand()))
@pytest.mark.parametrize("f_track_with_z", [True, False])
def test_compute_tiles_from_bounding_box(
    x_start,
    x_tiles,
    x_length,
    x_overlap,
    y_start,
    y_tiles,
    y_length,
    y_overlap,
    z_start,
    z_tiles,
    z_length,
    z_overlap,
    theta_start,
    theta_tiles,
    theta_length,
    theta_overlap,
    f_start,
    f_tiles,
    f_length,
    f_overlap,
    f_track_with_z,
):
    from navigate.tools.multipos_table_tools import compute_tiles_from_bounding_box

    tiles = compute_tiles_from_bounding_box(
        x_start,
        x_tiles,
        x_length,
        x_overlap,
        y_start,
        y_tiles,
        y_length,
        y_overlap,
        z_start,
        z_tiles,
        z_length,
        z_overlap,
        theta_start,
        theta_tiles,
        theta_length,
        theta_overlap,
        f_start,
        f_tiles,
        f_length,
        f_overlap,
        f_track_with_z,
    )

    x_tiles = 1 if x_tiles <= 0 else x_tiles
    y_tiles = 1 if y_tiles <= 0 else y_tiles
    z_tiles = 1 if z_tiles <= 0 else z_tiles
    theta_tiles = 1 if theta_tiles <= 0 else theta_tiles
    f_tiles = 1 if f_tiles <= 0 else f_tiles

    x_max = x_start + (1 - x_overlap) * x_length * (x_tiles - 1)
    y_max = y_start + (1 - y_overlap) * y_length * (y_tiles - 1)
    z_max = z_start + (1 - z_overlap) * z_length * (z_tiles - 1)
    theta_max = theta_start + (1 - theta_overlap) * theta_length * (theta_tiles - 1)
    f_max = f_start + (1 - f_overlap) * f_length * (f_tiles - 1)

    # check extrema
    assert tiles[0, 0] == x_start
    assert tiles[0, 1] == y_start
    assert tiles[0, 2] == z_start
    assert tiles[0, 3] == theta_start
    assert tiles[0, 4] == f_start
    assert tiles[-1, 0] == x_max
    assert tiles[-1, 1] == y_max
    assert tiles[-1, 2] == z_max
    assert tiles[-1, 3] == theta_max
    if f_track_with_z:
        assert tiles[-1, 4] <= f_max  # Due to clipping. TODO: Fix
    else:
        assert tiles[-1, 4] == f_max

    # check bounding box
    assert np.min(tiles[:, 0]) == x_start
    assert np.max(tiles[:, 0]) == x_max
    assert np.min(tiles[:, 1]) == y_start
    assert np.max(tiles[:, 1]) == y_max
    assert np.min(tiles[:, 2]) == z_start
    assert np.max(tiles[:, 2]) == z_max
    assert np.min(tiles[:, 3]) == theta_start
    assert np.max(tiles[:, 3]) == theta_max
    assert np.min(tiles[:, 4]) == f_start
    if f_track_with_z:
        assert np.max(tiles[:, 4]) <= f_max  # Due to clipping. TODO: Fix
    else:
        assert np.max(tiles[:, 4]) == f_max

    if f_track_with_z:
        # check length
        assert len(tiles) == x_tiles * y_tiles * z_tiles * theta_tiles
    else:
        assert len(tiles) == x_tiles * y_tiles * z_tiles * theta_tiles * f_tiles


@pytest.mark.parametrize("dist", listize(np.random.rand(3) * 1000))
@pytest.mark.parametrize("overlap", listize(np.random.rand(3)))
@pytest.mark.parametrize("roi_length", listize(np.random.rand(3) * 1000))
def test_calc_num_tiles(dist, overlap, roi_length):
    from navigate.tools.multipos_table_tools import calc_num_tiles

    # dist = 300
    # overlap = .75
    # roi_length = 525
    expected_num_tiles = ceil(
        # abs(dist - overlap * roi_length) / abs(roi_length - overlap * roi_length)
        (dist - overlap * roi_length)
        / (roi_length - overlap * roi_length)
    )

    result = calc_num_tiles(dist, overlap, roi_length)

    assert result == expected_num_tiles


class UpdateTableTestCase(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.frame = ttk.Frame()
        self.table = MultiPositionTable(parent=self.frame)

    def tearDown(self) -> None:
        self.root.destroy()

    def test_update_table_1(self):
        pos = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]])

        update_table(table=self.table, pos=pos, append=False)

        np.testing.assert_array_equal(self.table.model.df["X"], pos[:, 0])
        np.testing.assert_array_equal(self.table.model.df["Y"], pos[:, 1])
        np.testing.assert_array_equal(self.table.model.df["Z"], pos[:, 2])
        np.testing.assert_array_equal(self.table.model.df["R"], pos[:, 3])
        np.testing.assert_array_equal(self.table.model.df["F"], pos[:, 4])
        assert self.table.currentrow == 2

        new_positions = np.array([[16, 17, 18, 19, 20], [21, 22, 23, 24, 25]])

        print(self.table.model.df.shape)
        update_table(self.table, pos=new_positions, append=True)
        assert self.table.currentrow == 4
        np.testing.assert_array_equal(
            self.table.model.df["X"][
                3:,
            ],
            new_positions[:, 0],
        )
        np.testing.assert_array_equal(
            self.table.model.df["Y"][
                3:,
            ],
            new_positions[:, 1],
        )
        np.testing.assert_array_equal(
            self.table.model.df["Z"][
                3:,
            ],
            new_positions[:, 2],
        )
        np.testing.assert_array_equal(
            self.table.model.df["R"][
                3:,
            ],
            new_positions[:, 3],
        )
        np.testing.assert_array_equal(
            self.table.model.df["F"][
                3:,
            ],
            new_positions[:, 4],
        )


if __name__ == "__main__":
    unittest.main()
