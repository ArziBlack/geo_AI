"""
Segment Anything Model (SAM) for object segmentation in map images.
Requires: pip install segment-anything opencv-python matplotlib torch torchvision
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor


class MapSegmenter:
    def __init__(self, model_type="vit_h", checkpoint_path="sam_vit_h_4b8939.pth"):
        """
        Initialize SAM model for map segmentation.
        
        Args:
            model_type: Model size - 'vit_h' (huge), 'vit_l' (large), or 'vit_b' (base)
            checkpoint_path: Path to the SAM checkpoint file
        """
        self.device = "cuda" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"
        self.sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.sam.to(device=self.device)
        
        # For automatic mask generation
        self.mask_generator = SamAutomaticMaskGenerator(self.sam)
        
        # For prompted segmentation
        self.predictor = SamPredictor(self.sam)
    
    def segment_automatic(self, image_path, min_area=100):
        """
        Automatically segment all objects in the image.
        
        Args:
            image_path: Path to the input image
            min_area: Minimum area threshold for masks
            
        Returns:
            List of mask dictionaries with segmentation info
        """
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        masks = self.mask_generator.generate(image)
        
        # Filter by area
        filtered_masks = [m for m in masks if m['area'] > min_area]
        
        # Sort by area (largest first)
        filtered_masks = sorted(filtered_masks, key=lambda x: x['area'], reverse=True)
        
        return filtered_masks, image

    def segment_with_points(self, image_path, point_coords, point_labels):
        """
        Segment objects using point prompts.
        
        Args:
            image_path: Path to the input image
            point_coords: Array of [x, y] coordinates, shape (N, 2)
            point_labels: Array of labels (1=foreground, 0=background), shape (N,)
            
        Returns:
            masks, scores, logits
        """
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image)
        
        masks, scores, logits = self.predictor.predict(
            point_coords=np.array(point_coords),
            point_labels=np.array(point_labels),
            multimask_output=True
        )
        
        return masks, scores, logits, image
    
    def segment_with_box(self, image_path, box_coords):
        """
        Segment objects using bounding box prompt.
        
        Args:
            image_path: Path to the input image
            box_coords: [x1, y1, x2, y2] bounding box coordinates
            
        Returns:
            masks, scores, logits
        """
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image)
        
        masks, scores, logits = self.predictor.predict(
            box=np.array(box_coords),
            multimask_output=True
        )
        
        return masks, scores, logits, image
    
    def visualize_masks(self, image, masks, save_path=None):
        """
        Visualize segmentation masks on the image.
        
        Args:
            image: Original RGB image
            masks: List of mask dictionaries or mask array
            save_path: Optional path to save the visualization
        """
        plt.figure(figsize=(12, 8))
        plt.imshow(image)
        
        if isinstance(masks, list):
            # Automatic masks
            for mask in masks:
                self._show_mask(mask['segmentation'], plt.gca())
        else:
            # Single mask array
            self._show_mask(masks, plt.gca())
        
        plt.axis('off')
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.show()
    
    def _show_mask(self, mask, ax, random_color=True):
        """Helper to display a single mask."""
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([30/255, 144/255, 255/255, 0.6])
        
        h, w = mask.shape[-2:]
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)
    
    def extract_objects(self, image_path, output_dir="extracted_objects"):
        """
        Extract individual segmented objects as separate images.
        
        Args:
            image_path: Path to the input image
            output_dir: Directory to save extracted objects
            
        Returns:
            List of extracted object info
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        masks, image = self.segment_automatic(image_path)
        
        extracted = []
        for idx, mask in enumerate(masks):
            segmentation = mask['segmentation']
            bbox = mask['bbox']  # [x, y, w, h]
            
            # Extract object using mask
            object_img = image.copy()
            object_img[~segmentation] = 255  # White background
            
            # Crop to bounding box
            x, y, w, h = [int(v) for v in bbox]
            cropped = object_img[y:y+h, x:x+w]
            
            # Save
            output_path = os.path.join(output_dir, f"object_{idx:03d}.png")
            cv2.imwrite(output_path, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
            
            extracted.append({
                'id': idx,
                'path': output_path,
                'bbox': bbox,
                'area': mask['area']
            })
        
        return extracted


def main():
    """Example usage for map image segmentation."""
    
    # Initialize segmenter
    # Download checkpoint from: https://github.com/facebookresearch/segment-anything#model-checkpoints
    segmenter = MapSegmenter(
        model_type="vit_h",
        checkpoint_path="sam_vit_h_4b8939.pth"
    )
    
    # Example 1: Automatic segmentation
    print("Running automatic segmentation...")
    masks, image = segmenter.segment_automatic("map_image.png", min_area=500)
    print(f"Found {len(masks)} objects")
    segmenter.visualize_masks(image, masks, save_path="segmented_map.png")
    
    # Example 2: Point-based segmentation (click on specific objects)
    print("\nRunning point-based segmentation...")
    point_coords = [[100, 200], [300, 400]]  # x, y coordinates
    point_labels = [1, 1]  # 1 = foreground
    masks, scores, _, image = segmenter.segment_with_points(
        "map_image.png", 
        point_coords, 
        point_labels
    )
    segmenter.visualize_masks(image, masks[0], save_path="point_segmented.png")
    
    # Example 3: Extract individual objects
    print("\nExtracting individual objects...")
    objects = segmenter.extract_objects("map_image.png")
    print(f"Extracted {len(objects)} objects to 'extracted_objects/' directory")


if __name__ == "__main__":
    main()
