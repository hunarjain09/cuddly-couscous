"""
Heatmap visualization for keyboard usage
Shows which keys are used most frequently
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from typing import Dict, List


class KeyboardHeatmap:
    """Generate heatmap visualizations of keyboard usage"""

    # QWERTY layout positions
    QWERTY_LAYOUT = [
        ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
        ['tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
        ['caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'enter'],
        ['shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'shift'],
        ['ctrl', 'alt', 'cmd', 'space', 'space', 'space', 'cmd', 'alt', 'ctrl']
    ]

    def __init__(self, key_counts: Dict[str, int]):
        """
        Initialize heatmap generator

        Args:
            key_counts: Dict mapping keys to usage counts
        """
        self.key_counts = key_counts
        self.total_keys = sum(key_counts.values())

    def generate_heatmap(self, output_file: str = 'keyboard_heatmap.png'):
        """
        Generate and save keyboard heatmap

        Args:
            output_file: Path to save image
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 6))
        fig.patch.set_facecolor('white')

        # Create custom colormap (white -> yellow -> orange -> red)
        colors = ['#ffffff', '#fff3cd', '#ffd700', '#ff8c00', '#ff0000']
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list('heat', colors, N=n_bins)

        # Calculate normalized values for each key
        max_count = max(self.key_counts.values()) if self.key_counts else 1

        # Draw keyboard
        y_offset = len(self.QWERTY_LAYOUT) - 1
        for row_idx, row in enumerate(self.QWERTY_LAYOUT):
            x_offset = 0

            for key in row:
                # Get count for this key
                count = self.key_counts.get(key, 0)
                normalized = count / max_count if max_count > 0 else 0

                # Determine key width
                if key == 'space':
                    width = 3
                elif key in ['tab', 'caps', 'enter', 'shift', 'backspace']:
                    width = 1.5
                else:
                    width = 1

                # Draw key
                color = cmap(normalized)
                rect = mpatches.Rectangle(
                    (x_offset, y_offset - row_idx),
                    width, 0.9,
                    linewidth=1,
                    edgecolor='black',
                    facecolor=color
                )
                ax.add_patch(rect)

                # Add label
                label = key.upper() if len(key) == 1 else key[:4]
                ax.text(
                    x_offset + width / 2,
                    y_offset - row_idx + 0.45,
                    label,
                    ha='center',
                    va='center',
                    fontsize=8,
                    fontweight='bold'
                )

                # Add count if significant
                if count > 0:
                    ax.text(
                        x_offset + width / 2,
                        y_offset - row_idx + 0.15,
                        str(count),
                        ha='center',
                        va='center',
                        fontsize=6,
                        color='gray'
                    )

                x_offset += width + 0.1

        # Set axis properties
        ax.set_xlim(-0.5, 15)
        ax.set_ylim(-0.5, len(self.QWERTY_LAYOUT))
        ax.set_aspect('equal')
        ax.axis('off')

        # Add title
        plt.title('Keyboard Usage Heatmap', fontsize=16, fontweight='bold', pad=20)

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max_count))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.05, aspect=30)
        cbar.set_label('Key Press Count', fontsize=10)

        # Save
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Heatmap saved to: {output_file}")


class VoyagerHeatmap:
    """Generate heatmap for Voyager layout"""

    def __init__(self, key_counts: Dict[str, int]):
        self.key_counts = key_counts
        self.total_keys = sum(key_counts.values())

    def generate_split_heatmap(self, output_file: str = 'voyager_heatmap.png'):
        """Generate split keyboard heatmap for Voyager"""
        # Create figure with two subplots (left and right hand)
        fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 6))
        fig.patch.set_facecolor('white')

        # Voyager layout (simplified)
        left_hand = [
            ['esc', '[', '(', '-', ')', ']'],
            ['`', 'q', 'w', 'f', 'p', 'g'],
            ['+', 'a', 'r', 's', 't', 'd'],
            ['~', 'z', 'x', 'c', 'v', 'b'],
            ['L1', 'L2', 'spc', 'ent', 'sft']
        ]

        right_hand = [
            ['<', '/', '?', '\\', '=', 'del'],
            ['j', 'l', 'u', 'y', ';', '|'],
            ['h', 'n', 'e', 'i', 'o', "'"],
            ['k', 'm', ',', '.', '/', '!'],
            ['ctl', 'cmd', 'L3', 'alt', 'L5']
        ]

        # Draw both hands
        self._draw_hand(ax_left, left_hand, 'Left Hand')
        self._draw_hand(ax_right, right_hand, 'Right Hand')

        plt.suptitle('Voyager Keyboard Usage', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Voyager heatmap saved to: {output_file}")

    def _draw_hand(self, ax, layout, title):
        """Draw one hand of the keyboard"""
        colors = ['#ffffff', '#fff3cd', '#ffd700', '#ff8c00', '#ff0000']
        cmap = LinearSegmentedColormap.from_list('heat', colors, N=100)

        max_count = max(self.key_counts.values()) if self.key_counts else 1

        for row_idx, row in enumerate(layout):
            for col_idx, key in enumerate(row):
                count = self.key_counts.get(key, 0)
                normalized = count / max_count if max_count > 0 else 0

                color = cmap(normalized)
                rect = mpatches.Rectangle(
                    (col_idx, len(layout) - row_idx - 1),
                    0.9, 0.9,
                    linewidth=1,
                    edgecolor='black',
                    facecolor=color
                )
                ax.add_patch(rect)

                # Label
                ax.text(
                    col_idx + 0.45,
                    len(layout) - row_idx - 0.55,
                    key[:3],
                    ha='center',
                    va='center',
                    fontsize=7,
                    fontweight='bold'
                )

        ax.set_xlim(-0.1, 6)
        ax.set_ylim(-0.1, len(layout))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=12)
