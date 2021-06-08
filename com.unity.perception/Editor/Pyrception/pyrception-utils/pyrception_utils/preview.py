import argparse
import json
import os
import pathlib
from typing import Dict, List, Tuple

import numpy as np
import streamlit as st
import SessionState
import PIL
from PIL import ImageFont
from PIL.Image import Image
from PIL.ImageDraw import ImageDraw
from pyrception_utils import PyrceptionDataset

st.set_page_config(layout="wide")

#--------------------------------Custom component-----------------------------------------------------------------------

import streamlit.components.v1 as components

root_dir = os.path.dirname(os.path.abspath(__file__))
build_dir_slider = os.path.join(root_dir, "custom_components/slider/build")
build_dir_page_selector = os.path.join(root_dir, "custom_components/pageselector/build")
build_dir_go_to = os.path.join(root_dir, "custom_components/goto/build")
build_dir_item_selector = os.path.join(root_dir, "custom_components/itemselector/build")
build_dir_image_selector = os.path.join(root_dir, "custom_components/imageselector/build")
build_dir_json_viewer = os.path.join(root_dir, "custom_components/jsonviewer/build")
build_dir_item_selector_zoom = os.path.join(root_dir, "custom_components/itemselectorzoom/build")

_discrete_slider = components.declare_component(
    "discrete_slider",
    path=build_dir_slider
)

_page_selector = components.declare_component(
    "page_selector",
    path=build_dir_page_selector
)

_go_to = components.declare_component(
    "go_to",
    path=build_dir_go_to
)

_item_selector = components.declare_component(
    "item_selector",
    path=build_dir_item_selector
)

_image_selector = components.declare_component(
    "image_selector",
    path=build_dir_image_selector
)

_json_viewer = components.declare_component(
    "json_viewer",
    path=build_dir_json_viewer
)

_item_selector_zoom = components.declare_component(
    "item_selector_zoom",
    path=build_dir_item_selector_zoom
)


def discrete_slider(greeting, name, key, default=0):
    return _discrete_slider(greeting=greeting, name=name, default=default, key=key)


def page_selector(startAt, incrementAmt, key=0):
    return _page_selector(startAt=startAt, incrementAmt=incrementAmt, key=key, default=0)


def go_to(key=0):
    return _go_to(key=key, default=0)


def item_selector(startAt, incrementAmt, datasetSize, key=0):
    return _item_selector(startAt=startAt, incrementAmt=incrementAmt, datasetSize=datasetSize, key=key, default=startAt)


def image_selector(index, key=0):
    return _image_selector(index=index, key=key, default=index)


def json_viewer(metadata, key=0):
    return _json_viewer(jsonMetadata=metadata, key=key, default=0)


def item_selector_zoom(index, datasetSize, key=0):
    return _item_selector_zoom(index=index, datasetSize=datasetSize, key=key, default=index)
#-------------------------------------END-------------------------------------------------------------------------------

def list_datasets(path) -> List:
    """
    Lists the datasets in a diretory.
    :param path: path to a directory that contains dataset folders
    :type str:
    :return: A list of dataset directories.
    :rtype: List
    """
    datasets = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and item != "Unity":
            datasets.append(item)

    return datasets


def frame_selector_ui(dataset: PyrceptionDataset) -> int:
    """
    Frame selector streamlist widget to select which frame in the dataset to display
    :param dataset: the PyrceptionDataset
    :type PyrceptionDataset:
    :return: The image index
    :rtype: int
    """
    st.sidebar.markdown("# Image set")
    num_images = len(dataset)
    image_index = st.sidebar.slider("Image number", 0, num_images - 1)
    return image_index


def draw_image_with_boxes(
    image: Image,
    classes: Dict,
    labels: List,
    boxes: List[List],
    colors: Dict,
    header: str,
    description: str,
):
    """
    Draws an image in streamlit with labels and bounding boxes.

    :param image: the PIL image
    :type PIL:
    :param classes: the class dictionary
    :type Dict:
    :param labels: list of integer object labels for the frame
    :type List:
    :param boxes: List of bounding boxes (as a List of coordinates) for the frame
    :type List[List]:
    :param colors: class colors
    :type Dict:
    :param header: Image header
    :type str:
    :param description: Image description
    :type str:
    """
    image = image.copy()
    image_draw = ImageDraw(image)
    # draw bounding boxes
    path_to_font = pathlib.Path(__file__).parent.absolute()
    font = ImageFont.truetype(f"{path_to_font}/NairiNormal-m509.ttf", 15)

    for label, box in zip(labels, boxes):
        label = label - 1
        class_name = classes[label]
        image_draw.rectangle(box, outline=colors[class_name], width=2)
        image_draw.text(
            (box[0], box[1]), class_name, font=font, fill=colors[class_name]
        )
    #st.subheader(header)
    #st.markdown(description)
    #st.image(image, use_column_width=True)
    return image

def draw_image_with_semantic_segmentation(
    image: Image,
    height: int,
    width: int,
    segmentation: Image,
    header: str,
    description: str,
):
    """
    Draws an image in streamlit with labels and bounding boxes.

    :param image: the PIL image
    :type PIL:
    :param height: height of the image
    :type int:
    :param width: width of the image
    :type int:
    :param segmentation: Segmentation Image
    :type PIL:
    :param header: Image header
    :type str:
    :param description: Image description
    :type str:
    """
    # image_draw = ImageDraw(segmentation)
    rgba = np.array(segmentation.copy().convert("RGBA"))
    r,g,b,a = rgba.T
    black_areas = (r == 0) & (b == 0) & (g == 0) & (a == 255)
    other_areas = (r != 0) | (b != 0) | (g != 0)
    rgba[...,0:4][black_areas.T] = (0,0,0,0)
    rgba[...,-1][other_areas.T] = int(0.6 * 255)

    foreground = PIL.Image.fromarray(rgba)
    image = image.copy()
    image.paste(foreground,(0,0),foreground)
    return image

def draw_image_stacked(
    image: Image,
    classes: Dict,
    labels: List,
    boxes: List[List],
    colors: Dict,
    header: str,
    description: str,
    height: int,
    width: int,
    segmentation: Image,

):
    image = image.copy()
    color_intensity = st.sidebar.slider('color intensity 2 (%)', 0, 100, 65);
    alpha = color_intensity / 100;

    for x in range(0, width - 1):
        for y in range(0, height - 1):
            (seg_r, seg_g, seg_b) = segmentation.getpixel((x, y))
            (r, g, b) = image.getpixel((x, y))
            # if it isn't a black pixel in the segmentation image then highlight it with the segmentation color
            if seg_r != 0 or seg_g != 0 or seg_b != 0:
                image.putpixel((x, y),
                               (int((1 - alpha) * r + alpha * seg_r),
                                int((1 - alpha) * g + alpha * seg_g),
                                int((1 - alpha) * b + alpha * seg_b)))

    image_draw = ImageDraw(image)
    # draw bounding boxes
    path_to_font = pathlib.Path(__file__).parent.absolute()
    font = ImageFont.truetype(f"{path_to_font}/NairiNormal-m509.ttf", 15)

    for label, box in zip(labels, boxes):
        label = label - 1
        class_name = classes[label]
        image_draw.rectangle(box, outline=colors[class_name], width=2)
        image_draw.text(
            (box[0], box[1]), class_name, font=font, fill=colors[class_name]
        )

    st.subheader(header)
    st.markdown(description)
    st.image(image, use_column_width=True)


def display_count(
    header: str,
    description: str,
):
    """
    :param header: Image header
    :type str:
    :param description: Image description
    :type str:
    """
    return
@st.cache(show_spinner=True, allow_output_mutation=True)
def load_perception_dataset(path: str) -> Tuple:
    """
    Loads the perception dataset in the cache and caches the random bounding box color scheme.
    :param path: Dataset path
    :type str:
    :return: A tuple with the colors and PyrceptionDataset object as (colors, dataset)
    :rtype: Tuple
    """
    dataset = PyrceptionDataset(data_dir=path)
    classes = dataset.classes
    colors = {name: tuple(np.random.randint(128, 255, size=3)) for name in classes}
    return colors, dataset


def preview_dataset(base_dataset_dir: str):
    """
    Adds streamlit components to the app to construct the dataset preview.

    :param base_dataset_dir: The directory that contains the perceptions datasets.
    :type str:
    """
    #st.markdown("# Synthetic Dataset Preview\n ## Unity Technologies ")
    dataset_name = st.sidebar.selectbox(
        "Please select a dataset...", list_datasets(base_dataset_dir)
    )

    if dataset_name is not None:
        labelers = {'semantic_segmentation': st.sidebar.checkbox("Semantic Segmentation", key="ss"),
                    'bounding_boxes_2d': st.sidebar.checkbox("Bounding Boxes", key="bb2d")}

        colors, dataset = load_perception_dataset(
            os.path.join(base_dataset_dir, dataset_name)
        )

        session_state = SessionState.get(image='-1', start_at='0', num_cols='3')
        index = int(session_state.image)
        if index >= 0:
            dataset_path = os.path.join(base_dataset_dir, dataset_name)
            zoom(index, colors, dataset, session_state, labelers, dataset_path)
        else:
            num_rows = 5
            grid_view(num_rows, colors, dataset, session_state, labelers)


def grid_view(num_rows, colors, dataset, session_state, labelers):
    header = st.beta_columns([2/3, 1/3])
    num_cols = header[1].slider(label="Image per row: ", min_value=1, max_value=5, step=1, value=int(session_state.num_cols))
    session_state.num_cols = num_cols
    with header[0]:
        start_at = item_selector(int(session_state.start_at), num_cols * num_rows, len(dataset))
        session_state.start_at = start_at

    cols = st.beta_columns(num_cols)

    for i in range(start_at, min(start_at + (num_cols * num_rows), len(dataset))):
        classes = dataset.classes
        image, segmentation, target = dataset[i]
        labels = target["labels"]
        boxes = target["boxes"]

        if labelers['semantic_segmentation']:
            image = draw_image_with_semantic_segmentation(
                image, dataset.metadata.image_size[0], dataset.metadata.image_size[1], segmentation, "Semantic Segmentation Preview", ""
            )
        if labelers['bounding_boxes_2d']:
            image = draw_image_with_boxes(
                image, classes, labels, boxes, colors, "Bounding Boxes Preview", ""
            )
        container = cols[(i - (start_at % num_cols)) % num_cols].beta_container()
        container.write("Capture #" + str(i))
        expand_image = container.button(label="Expand image", key="exp"+str(i))
        container.image(image, caption=str(i), use_column_width=True)
        if expand_image:
            session_state.image = i
            st.experimental_rerun()


def zoom(index, colors, dataset, session_state, labelers, dataset_path):
    classes = dataset.classes
    image, segmentation, target = dataset[index]
    labels = target["labels"]
    boxes = target["boxes"]

    header = st.beta_columns([0.2, 0.6, 0.2])

    if header[0].button('< Back to Grid view'):
        session_state.image = -1
        st.experimental_rerun()

    with header[1]:
        new_index = item_selector_zoom(index, len(dataset))
        if not new_index == index:
            session_state.image = new_index
            st.experimental_rerun()

    if labelers['semantic_segmentation']:
        image = draw_image_with_semantic_segmentation(
            image, dataset.metadata.image_size[0], dataset.metadata.image_size[1], segmentation, "Semantic Segmentation Preview", ""
        )
    if labelers['bounding_boxes_2d']:
        image = draw_image_with_boxes(
            image, classes, labels, boxes, colors, "Bounding Boxes Preview", ""
        )

    layout = st.beta_columns([0.7, 0.3])
    layout[0].image(image, use_column_width=True)
    layout[1].title("JSON metadata")

    captures_dir = None
    for directory in os.walk(dataset_path):
        if "Dataset" in directory[0] and "." not in directory[0][1:]:
            captures_dir = directory[0]
            break

    file_num = index // 150
    postfix = ('000' + str(file_num))
    postfix = postfix[len(postfix) - 3:]
    path_to_captures = os.path.join(os.path.abspath(captures_dir), "captures_" + postfix + ".json")
    with layout[1]:
        json_file = json.load(open(path_to_captures, "r"))
        json_viewer(json.dumps(json_file["captures"][index]))


def preview_app(args):
    """
    Starts the dataset preview app.

    :param args: Arguments for the app, such as dataset
    :type args: Namespace
    """
    dataset_dir = args.data
    if dataset_dir is not None:
        st.sidebar.title("Pyrception Dataset Preview")
        preview_dataset(dataset_dir)
    else:
        raise ValueError("Please specify the path to the main dataset directory!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=str)
    args = parser.parse_args()
    st.markdown('<style>button.css-9eqr5v{display: none}</style>', unsafe_allow_html=True)
    #st.markdown('<script type="application/javascript"> function resizeIFrameToFitContent( iFrameme ) { iFrame.width  = '
    #            'iFrame.contentWindow.document.body.scrollWidth;iFrame.height = '
    #            'iFrame.contentWindow.document.body.scrollHeight;} window.addEventListener(\'DOMContentLoaded\', '
    #            'function(e) { var iFrame = document.getElementById( \'iFrame1\' ); resizeIFrameToFitContent( iFrame '
    #            '); var iframes = document.querySelectorAll("iframe"); for( var i = 0; i < iframes.length; i++) { '
    #            'resizeIFrameToFitContent( iframes[i] );} } ); </script>', unsafe_allow_html=True)
    preview_app(args)
