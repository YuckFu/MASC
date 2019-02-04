import numpy as np
import os
from plyfile import PlyData, PlyElement
import heapq
import sys

remapper = np.full(150, fill_value=-100, dtype=np.int32)
mapper = np.zeros(21, dtype=np.int32)
label_subset = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 24, 28, 33, 34, 36, 39]
for i, x in enumerate(label_subset):
    remapper[x] = i
    mapper[i] = x
    continue


def write_ply_color(filename, coords, faces, colors):
    
    header = """ply
format ascii 1.0
element vertex """
    header += str(len(coords))
    header += """
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element face """
    header += str(len(faces))
    header += """
property list uchar int vertex_index
end_header
"""

    with open(filename, 'w') as f:
        f.write(header)
        for coord, color in zip(coords, colors):
            for value in coord:
                f.write(str(value) + ' ')
                continue
            for value in color[:3]:
                f.write(str(value) + ' ')
                continue            
            f.write('\n')
            continue
        for face in faces:
            f.write('3 ' + str(face[0]) + ' ' + str(face[1]) + ' ' + str(face[2]) + '\n')
            continue
        pass
    return

def write_ply_label(filename, coords, faces, labels, visualize_boundary=True, debug_index=-1):
    if visualize_boundary:
        valid_indices = np.logical_and(labels[faces[:, 0]] == labels[faces[:, 1]], labels[faces[:, 0]] == labels[faces[:, 2]])
        #print(coords.min(0), coords.max(0))
        #valid_indices = np.logical_or(np.logical_or(np.all(coords[faces[:, 0]] == coords[faces[:, 1]], axis=-1), np.all(coords[faces[:, 0]] == coords[faces[:, 2]], axis=-1)), np.all(coords[faces[:, 1]] == coords[faces[:, 2]], axis=-1))
        faces = faces[valid_indices]
        pass
    if debug_index != -1:
        valid_indices = np.logical_and(np.logical_and(labels[faces[:, 0]] == debug_index, labels[faces[:, 1]] == debug_index), labels[faces[:, 2]] == debug_index)
        faces = faces[valid_indices]        
        #coords = coords[labels == debug_index]
        # print(len(faces), (labels == debug_index).sum(), [(labels[faces[:, c]] == debug_index).sum() for c in range(3)])        
        # print(len(np.unique(coords[:, 0] * 4096 * 4096 + coords[:, 1] * 4096 + coords[:, 2])))
        # exit(1)
        if len(faces) == 0:
            return
        coords = np.concatenate([coords[face] for face in faces], axis=0)
        faces = np.arange(len(faces) * 3).reshape((-1, 3))
        labels = np.full(len(coords), fill_value=debug_index)
        pass
    
    header = """ply
format ascii 1.0
element vertex """
    header += str(len(coords))
    header += """
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element face """
    header += str(len(faces))
    header += """
property list uchar int vertex_index
end_header
"""
    
    np.random.seed(1)
    color_map = np.random.randint(256, size=(labels.max() + 2, 3), dtype=np.uint8)
    #labels[labels == -100] = -1
    color_map[-1] = 255
    label_colors = color_map[labels]
    with open(filename, 'w') as f:
        f.write(header)
        for coord, color in zip(coords, label_colors):
            for value in coord:
                f.write(str(value) + ' ')
                continue
            for value in color:
                f.write(str(value) + ' ')
                continue            
            f.write('\n')            
            continue
        for face in faces:
            f.write('3 ' + str(face[0]) + ' ' + str(face[1]) + ' ' + str(face[2]) + '\n')
            continue        
        pass
    return

def write_ply_edge(filename, coords, edges, labels, augmented_edges=[]):
    # edges = np.concatenate([faces[:, [0, 1]], faces[:, [0, 2]], faces[:, [1, 2]]], axis=0)
    # if len(augmented_edges) > 0:
    #     edges = np.concatenate([edges, augmented_edges], axis=0)
    #     pass
    if True:
        valid_indices = np.abs(coords[edges[:, 0]] - coords[edges[:, 1]]).sum(-1) == 1
        #valid_indices = np.logical_or(valid_indices, np.abs(coords[edges[:, 0]] // 2 - coords[edges[:, 1]] // 2).sum(-1) == 1)
        edges = edges[valid_indices]
        pass
    
    header = """ply
format ascii 1.0
element vertex """
    header += str(len(coords))
    header += """
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element edge """
    header += str(len(edges))
    header += """
property int vertex1
property int vertex2
property uchar red
property uchar green
property uchar blue
end_header
"""

    np.random.seed(1)
    color_map = np.random.randint(256, size=(labels.max() + 2, 3), dtype=np.uint8)
    #labels[labels == -100] = -1
    color_map[-1] = 255
    label_colors = color_map[labels]
    
    edge_colors = np.zeros((len(edges), 3), dtype=np.uint8)
    distances = np.abs(coords[edges[:, 0]] - coords[edges[:, 1]]).sum(-1)
    edge_colors[distances == 1] = 255
    edge_colors[distances > 1] = np.array([255, 0, 0])
    with open(filename, 'w') as f:
        f.write(header)
        for coord, color in zip(coords, label_colors):
            for value in coord:
                f.write(str(value) + ' ')
                continue
            for value in color:
                f.write(str(value) + ' ')
                continue            
            f.write('\n')            
            continue
        for edge, color in zip(edges, edge_colors):
            f.write(str(edge[0]) + ' ' + str(edge[1]) + ' ' + str(color[0]) + ' ' + str(color[1]) + ' ' + str(color[2]) + '\n')
            continue        
        pass
    return

def write_ply_neighbor(filename, coords, neighbors, masks, size=4096):
    valid_mask = masks.sum(-1) > 0.5
    coords = coords[valid_mask]
    neighbors = (neighbors[valid_mask] > 0.95).astype(np.int32)
    masks = masks[valid_mask]        

    index_map = {}
    for index, coord in enumerate(coords):
        index_map[toIndex(coord, size)] = index
        continue
    
    valid_edges = []
    coord_offsets = np.array([[-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1]])    
    for index, coord in enumerate(coords):
        neighbor = neighbors[index]
        mask = masks[index] > 0.5
        for offset, label in zip(coord_offsets[mask], neighbor[mask]):
            neighbor_coord = coord + offset
            neighbor_index = toIndex(neighbor_coord, size)
            if neighbor_index not in index_map:
                continue
            neighbor_index = index_map[neighbor_index]
            if label == 0:
                continue
            valid_edges.append((index, neighbor_index, label))
            continue
        continue

    edges = np.array(valid_edges)
    color_map = np.array([[255, 0, 0], [255, 255, 255]])
    edge_colors = color_map[edges[:, 2]]
    edges = edges[:, :2]
    #edge_colors = np.full((len(edges), 3), fill_value=255, dtype=np.uint8)

    coords *= 4096 // size
    
    header = """ply
format ascii 1.0
element vertex """
    header += str(len(coords))
    header += """
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element edge """
    header += str(len(edges))
    header += """
property int vertex1
property int vertex2
property uchar red
property uchar green
property uchar blue
end_header
"""

    np.random.seed(1)
    #color_map = np.random.randint(256, size=(labels.max() + 2, 3), dtype=np.uint8)
    #labels[labels == -100] = -1
    #color_map[-1] = 255
    label_colors = np.full(coords.shape, fill_value=255, dtype=np.uint8)
    
    with open(filename, 'w') as f:
        f.write(header)
        for coord, color in zip(coords, label_colors):
            for value in coord:
                f.write(str(value) + ' ')
                continue
            for value in color:
                f.write(str(value) + ' ')
                continue            
            f.write('\n')            
            continue
        for edge, color in zip(edges, edge_colors):
            f.write(str(edge[0]) + ' ' + str(edge[1]) + ' ' + str(color[0]) + ' ' + str(color[1]) + ' ' + str(color[2]) + '\n')
            continue        
        pass
    return


def writeSemantics(filename, semantics):
    semantics = mapper[semantics]    
    np.savetxt(filename, semantics, fmt='%d')
    return

def writeInstances(path, scene_id, instances, semantics, instance_info):
    semantics = mapper[semantics]
    print(scene_id, 'num instances', instances.max() + 1)
    #for instance_index in np.unique(instances):
    if len(instance_info) == 0:
        instance_info = []
        for instance_index in range(instances.max() + 1):
            instance_mask = instances == instance_index
            semantic_labels = semantics[instance_mask]
            semantic_labels, counts = np.unique(semantic_labels, return_counts=True)
            instance_info.append((instance_mask, semantic_labels[counts.argmax()], float(counts.max()) / counts.sum()))
            continue
    else:
        valid_instance_info = []
        for mask, label, confidence in instance_info:
            if label == 20:
                continue
            valid_instance_info.append((mask, mapper[label], confidence))
            continue
        instance_info = valid_instance_info
        pass
    
    with open(path + '/' + scene_id + '.txt', 'w') as f:
        for instance_index, (mask, label, confidence) in enumerate(instance_info):
            f.write('pred_mask/' + scene_id + '_' + str(instance_index) + '.txt ' + str(label) + ' ' + str(confidence) + '\n')
            np.savetxt(path + '/pred_mask/' + scene_id + '_' + str(instance_index) + '.txt', mask, fmt='%d')
            continue
        pass
    #return
    if False:
        instance_segmentation = np.zeros(len(instances), dtype=np.int32)
        for instance_index, instance_mask in enumerate(instance_masks):
            instance_segmentation[instance_mask] = instance_index
            continue
        np.save(options.test_dir + '/pred/' + scene_id + '.npy', instance_segmentation)
        pass    
    return instance_info

def findInstancesSemanticsLabels(edges, semantics, labels=[10, 13, 15, 17, 18], instance_info=[]):
    #DEBUG_INFO = ['cabinet', 2, 3, 'bed', 3, 4, 'chair', 4, 5, 'sofa', 5, 6, 'table', 6, 7, 'door', 7, 8, 'window', 8, 9, 'bookshelf', 9, 10, 'picture', 10, 11, 'counter', 11, 12, 'desk', 12, 14, 'curtain', 13, 16, 'refrigerator', 14, 24, 'shower curtain', 15, 28, 'toilet', 16, 33, 'sink', 17, 34, 'bathtub', 18, 36, 'otherfurniture', 19, 39]    
    #instances = np.full(len(semantics), fill_value=-1, dtype=np.int32)
    ranges = np.arange(len(semantics), dtype=np.int32)
    valid_mask = semantics[edges[:, 0]] == semantics[edges[:, 1]]
    #source_indices = edges.max(-1)[valid_mask]
    #target_indices = edges.min(-1)[valid_mask]
    #print(np.unique(semantics))
    edges = edges[valid_mask]
    #edges = np.concatenate([edges, edges[:, [1, 0]]], axis=0)
    
    # for index, label in enumerate(labels):
    #     mask = semantics == label
    #     #instances[mask] = ranges[mask] + index * len(semantics)
    #     #instances[mask] = index
    #     instances[mask] = ranges[mask]
    #     continue
    
    # while True:
    #     new_instances = instances.copy()
    #     new_instances[edges[:, 0]] = np.minimum(instances[edges[:, 0]], instances[edges[:, 1]])
    #     new_instances[edges[:, 1]] = np.minimum(instances[edges[:, 0]], instances[edges[:, 1]])
        
    #     #new_instances[source_indices] = instances[target_indices]
    #     if np.all(new_instances == instances):
    #         break
    #     instances = new_instances
    #     continue
    
    instance_masks = []
    for label in labels:
        valid_mask = semantics[edges[:, 0]] == label
        semantic_edges = edges[valid_mask]
        existing_masks = [info[0] for info in instance_info if info[1] == label]
        existing_mask_areas = [mask.sum() for mask in existing_masks]        
        if len(existing_masks) > 0:
            print(existing_masks[0].dtype)
            exit(1)
        while len(semantic_edges) >= 100:
            instances = np.zeros(len(semantics), dtype=np.bool)
            instances[semantic_edges[0]] = 1
            while True:
                valid_mask = np.logical_and(instances[semantic_edges[:, 0]], np.logical_not(instances[semantic_edges[:, 1]]))
                neighbors = semantic_edges[:, 1][valid_mask]
                if len(neighbors) == 0:
                    semantic_edges = semantic_edges[np.logical_not(instances[semantic_edges[:, 0]])]
                    break
                instances[neighbors] = 1
                continue
            instance_area = instances.sum()
            if instance_area < 100:
                continue
            if len(existing_masks) > 0:
                intersections = [np.logical_and(mask, instances).sum() for mask in existing_masks]
                IOUs = [float(intersection) / max(existing_mask_area + instance_area - intersection, 1) for intersection, existing_mask_area in zip(intersections, existing_mask_areas)]
                if max(IOUs) > 0.5:
                    continue
                pass
            instance_masks.append(instances)
            continue
        continue            
        
    # unique_instances, instances, counts = np.unique(instances, return_inverse=True, return_counts=True)
    # index_map = np.full(len(unique_instances), fill_value=-1, dtype=np.int32)
    # new_index = 0
    # for index, (instance, count) in enumerate(zip(unique_instances, counts)):
    #     if instance < 0 or count < 50:
    #         continue
    #     #print(semantics[(instances == index).nonzero()[0][0]], count)
    #     instance_info
    #     index_map[index] = new_index
    #     new_index += 1
    #     continue
    # instances = index_map[instances]
    instances = np.full(len(semantics), fill_value=-1, dtype=np.int32)
    for index, mask in enumerate(instance_masks):
        instances[mask] = index
        continue
    return instances, len(instance_masks)

def findInstancesSemantics(options, edges, semantics):
    #print(faces.shape, faces.min(), faces.max(), semantics.shape)
    #edges = np.concatenate([faces[:, [0, 1]], faces[:, [0, 2]], faces[:, [1, 2]]], axis=0)
    scores = semantics[edges[:, 0]] == semantics[edges[:, 1]]
    nodes = np.stack([np.arange(len(semantics), dtype=np.int32), np.arange(len(semantics))], axis=-1).tolist()
    nodes = [[[node[0], ], [], node[1]] for node in nodes]
    edges = np.concatenate([1 - np.expand_dims(scores, -1), edges], axis=-1).tolist()
    print((scores > 0.5).sum(), len(scores))
    edge_queue = []    
    for edge in edges:
        edge_queue.append(tuple(edge))
        nodes[edge[1]][1].append(edge[2])
        nodes[edge[2]][1].append(edge[1])
        continue
    heapq.heapify(edge_queue)
    threshold = 0.5
    while True:
        if len(edge_queue) == 0:
            break
        if len(edge_queue) % 100 == 0:
            print(len(edge_queue))
            pass
        edge = heapq.heappop(edge_queue)
        if edge[0] > threshold:
            break
        node_indices = []
        for node_index in edge[1:3]:
            visited_node_indices = []
            while nodes[node_index][-1] != node_index:
                visited_node_indices.append(node_index)                    
                node_index = nodes[node_index][-1]
                continue
            for _ in visited_node_indices:
                nodes[_][-1] = node_index
                continue
            node_indices.append(node_index)
            continue
        if node_indices[0] == node_indices[1]:
            continue
        nodes[node_indices[0]][0] += nodes[node_indices[1]][0]
        nodes[node_indices[1]][0] = []
        nodes[node_indices[1]][-1] = node_indices[0]
        continue
    
    instances = np.array([node[-1] for node in nodes])
    while True:
        new_instances = instances[instances]
        if np.all(new_instances == instances):
            break
        instances = new_instances
        continue
    
    _, instances = np.unique(instances, return_inverse=True)
    instance_labels, counts = np.unique(instances, return_counts=True)
    valid_labels = instance_labels[counts > 100]
    print('num valid instances', len(valid_labels))
    label_map = np.full(len(counts), fill_value=-1)
    for index, label in enumerate(valid_labels):
        label_map[label] = index
        continue
    instances = label_map[instances]
    
    return instances.astype(np.int32)

def toIndex(coord, size):
    return coord[0] * size * size + coord[1] * size + coord[2]
        
def toCoord(index, size):
    return np.array([index // (size * size), index // size % size, index % size])

def loadInstance(filename):
    with open(filename, 'r') as f:
        print('load instances', filename)
        for line_index, line in enumerate(f):
            mask = np.loadtxt('/'.join(filename.split('/')[:-1]) + '/' + line.split(' ')[0]).astype(np.int32)
            if line_index == 0:
                instances = mask - 1
            else:
                instances[mask > 0.5] = line_index
                pass
            continue
        pass
    return instances
                
def findInstances(coords, edges, semantics, neighbors, num_scales, num_cross_scales, full_scale=4096, num_neighbors=6, num_dimensions=3, print_info=True, cache_filename='', scene_id=''):
    debug = False
    if cache_filename != '':
        return np.load('cache/' + str(num_scales) + '/' + scene_id + '.npy'), []
        #return np.load('test/instances.npy'), []        
        instances = loadInstance(cache_filename)
        return instances, []

    num_scales = num_scales
    if False:
        num_scales = 1
        #neighbors[0] += np.random.random(neighbors[0].shape) * 0.05
        pass
    
    for scale in range(num_scales):
        offsets = [0, num_neighbors]
        for _ in range(scale + 1, min(num_scales, scale + num_cross_scales)):
            offsets.append(offsets[-1] + num_neighbors + 1)                
            continue
        neighbors[scale] = [np.array([])] * scale + [neighbors[scale][:, offsets[index]:offsets[index + 1]] for index in range(len(offsets) - 1)]
        #print(scale, [neighbor.shape for neighbor in neighbors[scale]])
        continue
    coord_offsets = np.array([[-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1]])
    
    if False:
        neighbors_0 = neighbors[1][1]
        coords = coords // pow(2, 1)
        size = full_scale // pow(2, 1)
        starting_index = np.random.randint(len(coords))
        print(starting_index)
        #starting_index = 114427
        coord_neighbors = {}                
        for coord, neighbor in zip(coords, neighbors_0):
            #coord_neighbors[toIndex(coord)] = neighbor.argmax() == np.arange(6)
            coord_neighbors[toIndex(coord, size)] = neighbor
            continue

        #offsets = np.array([[0, 0, -1], [0, 0, 1], [0, -1, 0], [0, 1, 0], [-1, 0, 0], [1, 0, 0]])
        instance = {toIndex(coords[starting_index], size): True}
        active_coords = [coords[starting_index]]
        while len(active_coords) > 0:
            new_coords = []
            for coord in active_coords:
                #neighbor = neighbors_0[toIndex(coord)]
                neighbor = coord_neighbors[toIndex(coord, size)]
                for offset in coord_offsets[neighbor > 0.5]:
                    neighbor_coord = coord + offset
                    neighbor_index = toIndex(neighbor_coord, size)
                    if neighbor_index in instance:
                        continue
                    instance[neighbor_index] = True
                    new_coords.append(neighbor_coord)
                    continue
                continue
            active_coords = new_coords
            continue

        instance_mask = {}        
        for index in instance.keys():
            instance_mask[index] = True
            continue
        instance = np.array([toCoord(index, size) for index in instance.keys()])
        print(instance.shape)
        write_ply('test/instance', instance, np.zeros(instance.shape), np.zeros(len(instance), dtype=np.int32), write_input=False)
        exit(1)
        pass

    # print(coords[38])
    # print(coords[1075])    
    # print(coords[1846])
    # print(neighbors[0][0][38])
    # print(neighbors[0][0][1075])
    # print(neighbors[0][0][1846])        
    # print(neighbors[1][1][1846])    
    # print(neighbors[1][1][1075])
    # exit(1)
    
    # count_dicts = [{}]
    # for scale in range(1, num_scales):
    #     size = full_scale // pow(2, scale)
    #     count_dict = {}
    #     scale_coords = coords // pow(2, scale)
    #     indices = scale_coords[:, 0] * size * size + scale_coords[:, 1] * size + scale_coords[:, 2]
                
    #     for index in indices:
    #         if index not in count_dict:
    #             count_dict[index] = 0
    #             pass
    #         count_dict[index] += 1
    #         continue
    #     count_dicts.append(count_dict)
    #     continue

    # coord_neighbors = []
    # for scale_index, scale_neighbors in neighbors:
    #     coord_neighbors.append([{toIndex(coord): neighbor for coord, neighbor in zip(coords, scale_neighbor)} for scale_neighbor in scale_neighbors])
    #     continue
    
    scale_count_thresholds = pow(4, np.arange(num_scales))
    connection_ratio_threshold = 0.2    

    coord_node_map = []
    for scale in range(num_scales):
        coord_node_map.append({toIndex(coord, full_scale // pow(2, scale)): node_index for node_index, coord in enumerate(coords // pow(2, scale))})
        continue    
        
    #print(faces.shape, faces.min(), faces.max(), semantics.shape)
    ori_node_mapping = np.arange(len(coords), dtype=np.int64)
    node_info = [({0: (np.expand_dims(coord, 0), np.array([node_index]))}, (np.arange(41) == semantics[node_index]).astype(np.float32)) for node_index, coord in enumerate(coords)]
    direction_multiplier = pow(2, np.arange(3))
    direction_mapping_dict = {-1: 0, 1: 1, -2: 2, 2: 3, -4: 4, 4:5, 0: 6}
    direction_mapping = np.zeros(9, dtype=np.int32)
    direction_index_mapping = np.array([-1, 1, -2, 2, -4, 4, 0])
    for direction, mapping in direction_mapping_dict.items():
        direction_mapping[direction + 4] = mapping
        continue

    if debug:
        ori_node_mapping = loadInstance(cache_filename)
        node_instances = [[] for _ in range(ori_node_mapping.max() + 1)]
        for ori_node, node in enumerate(ori_node_mapping):
            node_instances[node].append(ori_node)
            continue
        
        node_instances = [np.array(instance) for instance in node_instances]
        node_info = []
        for instance in node_instances:
            info = {}
            node_coords = coords[instance]
            labels = semantics[instance]
            unique_labels, counts = np.unique(labels, return_counts=True)
            label_counts = np.zeros(41)
            label_counts[unique_labels] = counts
            #print(instance, np.array([coord_node_map[0][toIndex(coord, full_scale)] for coord in node_coords]))
            #print('valid', np.all(neighbors[0][0][np.array([coord_node_map[0][toIndex(coord, full_scale)] for coord in node_coords])] == neighbors[0][0][instance]))
            #exit(1)
            info[0] = (node_coords, instance)
            for scale in range(1, num_scales):
                size = full_scale // pow(2, scale)
                node_coords = node_coords // 2
                indices = node_coords[:, 0] * size * size + node_coords[:, 1] * size + node_coords[:, 2]
                indices, mapping, counts = np.unique(indices, return_index=True, return_counts=True)
                valid_coords = []
                for index, coord_index, count in zip(indices, mapping, counts):
                    #if count >= count_dicts[scale][index] * 0.5:
                    if count >= scale_count_thresholds[scale]:
                        valid_coords.append(node_coords[coord_index])
                        pass
                    continue
                if len(valid_coords) > 0:
                    info[scale] = (valid_coords, np.array([coord_node_map[scale][toIndex(coord, full_scale // pow(2, scale))] for coord in valid_coords]))
                    pass
                pass
            node_info.append((info, label_counts))
            continue        
        debug = True
        print('num instances', len(node_info))
        for node_index, info in enumerate(node_info):
            print(node_index, info[1].argmax())
            continue
        pass

    # print(neighbors[0][0].shape, neighbors[0][0].max(-1).min())
    # valid_node_mask = neighbors[0][0].max(-1) > 0.5
    # print(edges.shape)
    # edges = edges[np.logical_and(valid_node_mask[edges[:, 0]], valid_node_mask[edges[:, 1]])]
    # print(valid_node_mask.sum(), edges.shape)    
    ori_edges = edges
    
    intermediate_instances = []
    iteration = 0
    while True:
        node_scores = {}
        instance_coord_maps = {}
        
        edges = ori_node_mapping[ori_edges]
        edges.sort(-1)
        edges = np.unique(edges[:, 0] * len(coords) + edges[:, 1])
        edges = np.stack([edges // len(coords), edges % len(coords)], axis=-1)
        edges = edges[np.logical_and(edges[:, 0] != edges[:, 1], np.all(edges >= 0, axis=-1))]
        # print(edges.max(), len(coords), len(node_info))
        for edge_index, edge in enumerate(edges):
            node_pair = edge
            # node_pair = [ori_node_mapping[node_index] for node_index in edge]
            # if node_pair[0] == node_pair[1]:
            #     continue
            # node_pair = (min(node_pair), max(node_pair))
            # if node_pair[0] in node_scores and node_pair[1] in node_scores[node_pair[0]]:
            #     continue
            
            semantic_similarity = ((node_info[node_pair[0]][1] / max(node_info[node_pair[0]][1].sum(), 1)) * (node_info[node_pair[1]][1] / max(node_info[node_pair[1]][1].sum(), 1))).sum()
            #if semantic_similarity < 0.5:
            #continue
            
            # label_counts = node_info[node_pair[0]][1] + node_info[node_pair[1]][1]
            # if label_counts.max() != label_counts.sum():
            #     for c in range(2):
            #         if node_pair[c] not in node_scores:
            #             node_scores[node_pair[c]] = {}
            #             pass
            #         node_scores[node_pair[c]][node_pair[1 - c]] = 0
            #         continue
            #     continue
            scores = []
            score_info = []
            #largest_scale = min([max(node_info[node_pair[0]][0].keys()) for c in range(2)])
            for scale_1, (coord_1, ori_node_indices_1) in node_info[node_pair[0]][0].items():
                for scale_2, (coord_2, ori_node_indices_2) in node_info[node_pair[1]][0].items():
                    if print_info:
                        sys.stdout.write('\r' + str(edge_index) + ' ' + str(len(edges)) + ' ' + str(scale_1) + ' ' + str(scale_2) + ' ' + str(len(coord_1)) + ' ' + str(len(coord_2)) + ' ')
                        pass
                    if scale_1 == scale_2:
                        if scale_1 > 2:
                            continue
                        if len(coord_1) <= 1000 and len(coord_2) <= 1000:
                        #if len(coord_1) * len(coord_2) <= 10000:
                            directions = (np.expand_dims(coord_2, 0) - np.expand_dims(coord_1, 1)).reshape((-1, num_dimensions))
                            distances = np.abs(directions).sum(-1)
                            direction_indices = np.dot(directions, direction_multiplier)
                            valid_mask = distances == 1
                            direction_indices = direction_indices[valid_mask]
                            indices_1 = np.expand_dims(ori_node_indices_1, 1).repeat(len(ori_node_indices_2), axis=1).reshape(-1)[valid_mask]
                            indices_2 = np.expand_dims(ori_node_indices_2, 0).repeat(len(ori_node_indices_1), axis=0).reshape(-1)[valid_mask]
                        else:
                            if len(coord_1) < len(coord_2):
                                coord_1, coord_2 = coord_2, coord_1
                                ori_node_indices_1, ori_node_indices_2 = ori_node_indices_2, ori_node_indices_1
                                cache_pair_index = 0
                            else:
                                cache_pair_index = 1
                                pass
                            if scale_2 in instance_coord_maps and node_pair[cache_pair_index] in instance_coord_maps[scale_2]:
                                instance_coord_map = instance_coord_maps[scale_2][node_pair[cache_pair_index]]
                            else:
                                if scale_2 not in instance_coord_maps:
                                    instance_coord_maps[scale_2] = {}
                                    pass
                                instance_coord_map = {toIndex(coord, full_scale // pow(2, scale_2)): ori_node_index for coord, ori_node_index in zip(coord_2, ori_node_indices_2)}
                                instance_coord_maps[scale_2][node_pair[cache_pair_index]] = instance_coord_map
                                pass
                            coord_neighbors = np.expand_dims(coord_1, 1) + coord_offsets
                            size = full_scale // pow(2, scale_2)
                            coord_neighbor_indices = coord_neighbors[:, :, 0] * size * size + coord_neighbors[:, :, 1] * size + coord_neighbors[:, :, 2]
                            indices_1, indices_2, direction_indices = [], [], []
                            for neighbor_index, (coord_index, ori_node_index) in enumerate(zip(coord_neighbor_indices.reshape(-1), np.expand_dims(ori_node_indices_1, axis=-1).repeat(num_neighbors, axis=-1).reshape(-1))):
                                if coord_index in instance_coord_map:
                                    indices_1.append(ori_node_index)                                    
                                    indices_2.append(instance_coord_map[coord_index])                                                                        
                                    direction_indices.append(direction_index_mapping[neighbor_index % num_neighbors])
                                    pass
                                continue
                            indices_1 = np.array(indices_1)
                            indices_2 = np.array(indices_2)
                            direction_indices = np.array(direction_indices)
                            pass
                            
                        # if node_pair == (106827, 109911):
                        #     print(indices_1, direction_indices, neighbors[scale_1][scale_2][indices_1])
                        #     print(neighbors[scale_1][scale_2][indices_1, direction_mapping[direction_indices + 4]])
                        #     exit(1)    
                        #distances = distances[distances == 1]
                        
                        instance_size = np.sqrt(float(min(len(coord_1), len(coord_2))))
                        if len(direction_indices) > round(instance_size * connection_ratio_threshold):
                            #scores.append((distances == 1) * (neighbors[scale_1][scale_2][edge[0]][direction_mapping[direction_indices]] + neighbors[scale_2][scale_1][edge[1]][direction_mapping[-direction_indices]]) / 2)
                            #score_info.append(np.full((len(direction_indices), 2), fill_value=scale_1))                            
                            scores.append(((neighbors[scale_1][scale_2][indices_1, direction_mapping[direction_indices + 4]] + neighbors[scale_2][scale_1][indices_2, direction_mapping[-direction_indices + 4]]) / 2).mean())
                            score_info.append(np.array([scale_1, scale_1]))
                        else:
                            if iteration >= 4:
                                #print(len(direction_indices), instance_size)
                                pass
                            pass                        
                        # for direction in directions:
                        #     distance = np.abs(direction).sum()
                        #     if distance == 0 and scale_1 == 0:
                        #         scores.append(1)
                        #     elif distance == 1:
                        #         direction_index = np.dot(direction, direction_multiplier)
                        #         #print(len(neighbors), len(neighbors[scale_1]), neighbors[scale_1][direction_mapping[direction_index]].shape)
                        #         scores.append((neighbors[scale_1][scale_2][direction_mapping[direction_index]][edge[0]] + neighbors[scale_2][scale_1][direction_mapping[-direction_index]][edge[1]]) / 2)
                        #         pass
                    elif abs(scale_1 - scale_2) <= num_cross_scales:
                        if scale_1 > scale_2:
                            scale_1, scale_2 = scale_2, scale_1
                            coord_1, coord_2 = coord_2, coord_1
                            ori_node_indices_1, ori_node_indices_2 = ori_node_indices_2, ori_node_indices_1
                            pass
                        coord_1 = coord_1 // pow(2, scale_2 - scale_1)
                        if len(coord_1) <= 1000 and len(coord_2) <= 1000:                        
                            #if len(coord_1) * len(coord_2) <= 10000:
                            directions = (np.expand_dims(coord_2, 0) - np.expand_dims(coord_1, 1)).reshape((-1, num_dimensions))
                            distances = np.abs(directions).sum(-1)
                            direction_indices = np.dot(directions, direction_multiplier)
                            valid_mask = distances <= 1
                            direction_indices = direction_indices[valid_mask]
                            indices_1 = np.expand_dims(ori_node_indices_1, 1).repeat(len(ori_node_indices_2), axis=1).reshape(-1)[valid_mask]
                        else:
                            if scale_2 in instance_coord_maps and node_pair[cache_pair_index] in instance_coord_maps[scale_2]:
                                instance_coord_map = instance_coord_maps[scale_2][node_pair[cache_pair_index]]
                            else:
                                if scale_2 not in instance_coord_maps:
                                    instance_coord_maps[scale_2] = {}
                                    pass
                                instance_coord_map = {toIndex(coord, full_scale // pow(2, scale_2)): ori_node_index for coord, ori_node_index in zip(coord_2, ori_node_indices_2)}
                                instance_coord_maps[scale_2][node_pair[cache_pair_index]] = instance_coord_map
                                pass
                            coord_neighbors = np.expand_dims(coord_1, 1) + coord_offsets
                            coord_neighbors = np.concatenate([coord_neighbors, np.expand_dims(coord_1, 1)], axis=1)
                            size = full_scale // pow(2, scale_2)
                            coord_neighbor_indices = coord_neighbors[:, :, 0] * size * size + coord_neighbors[:, :, 1] * size + coord_neighbors[:, :, 2]
                            indices_1, indices_2, direction_indices = [], [], []
                            for neighbor_index, (coord_index, ori_node_index) in enumerate(zip(coord_neighbor_indices.reshape(-1), np.expand_dims(ori_node_indices_1, axis=-1).repeat(num_neighbors + 1, axis=-1).reshape(-1))):
                                if coord_index in instance_coord_map:
                                    indices_1.append(ori_node_index)                                    
                                    direction_indices.append(direction_index_mapping[neighbor_index % (num_neighbors + 1)])
                                    pass
                                continue
                            indices_1 = np.array(indices_1)
                            direction_indices = np.array(direction_indices)
                            pass

                        if len(direction_indices) > 0:
                            #scores.append((distances == 0) * neighbors[scale_1][scale_2][indices_1, num_neighbors] + (distances == 1) * neighbors[scale_1][scale_2][indices_1, direction_mapping[direction_indices + 4]])
                            #print(indices_1, direction_indices, neighbors[scale_1][scale_2][indices_1, direction_mapping[direction_indices + 4]])
                            #exit(1)
                            #score_info.append(np.stack([np.full(len(direction_indices), fill_value=scale_1), np.full(len(direction_indices), fill_value=scale_2)], axis=-1))
                            scores.append(neighbors[scale_1][scale_2][indices_1, direction_mapping[direction_indices + 4]].mean())
                            score_info.append(np.array([scale_1, scale_2]))
                            pass
                        
                        # for direction in directions:
                        #     distance = np.abs(direction).sum()
                        #     if distance == 0:
                        #         scores.append(neighbors[scale_1][scale_2][num_neighbors][ori_node_index])
                        #     elif distance == 1:
                        #         direction_index = np.dot(direction, direction_multiplier)
                        #         scores.append(neighbors[scale_1][scale_2][direction_mapping[direction_index]][ori_node_index])
                        #         pass
                        #     continue
                        pass
                    continue
                continue
            if len(scores) > 0:
                #scores = np.concatenate(scores, axis=0)
                scores = np.array(scores)
                
                #score = scores.mean()
                score = scores[np.array(score_info).sum(-1).argmax()]

                if debug:
                    if node_info[node_pair[0]][1].argmax() == 4 and node_info[node_pair[1]][1].argmax() == 4:
                        print('bed')
                        print(scores)
                        exit(1)
                        pass
                if False:
                    score_info = np.stack(score_info, axis=0)
                    scores_0 = scores[np.all(score_info == 0, axis=-1)]
                    if len(scores_0) > 0:
                        if (scores_0.mean() > 0.5) != (score > 0.5):
                            #print(np.concatenate([np.expand_dims(scores, axis=-1), score_info], axis=-1))
                            print('difference')
                            print(node_pair)
                            print(node_info[node_pair[0]], node_info[node_pair[1]])
                            print(np.concatenate([np.expand_dims(scores, -1), score_info], axis=-1))
                            #exit(1)
                            pass
                    else:
                        print('no zero')
                        print(node_info[node_pair[0]], node_info[node_pair[1]])
                        print(scores, score_info)
                        #exit(1)                        
                        pass
                    pass
                
                for c in range(2):
                    if node_pair[c] not in node_scores:
                        node_scores[node_pair[c]] = {}
                        pass
                    #node_scores[node_pair[c]][node_pair[1 - c]] = score * semantic_similarity
                    node_scores[node_pair[c]][node_pair[1 - c]] = score
                    continue
                pass
            continue
        if print_info:
            print('')
            pass
        has_change = False
        node_mapping = np.arange(len(node_info), dtype=np.int64)
        for node, neighbor_scores in node_scores.items():
            max_score_neighbor = (0.5, -1)
            for neighbor, score in neighbor_scores.items():
                # if len(scores) == 0:
                #     continue
                # if len(node_scores) < 100:
                #     print(score)
                #     pass
                if score > max_score_neighbor[0]:
                    max_score_neighbor = [score, neighbor]
                    pass
                continue
            if max_score_neighbor[1] >= 0:
                node_mapping[node] = max_score_neighbor[1]
                has_change = True
                pass
            continue
        if not has_change:
            break

        # for ori_node, node in enumerate(node_mapping):
        #     if (toIndex(coords[ori_node]) in instance_mask) != (toIndex(coords[node]) in instance_mask):
        #         print(toIndex(coords[ori_node]) in instance_mask, toIndex(coords[node]) in instance_mask, ori_node, node, coords[ori_node], coords[node], neighbors[0][0][ori_node], neighbors[0][0][node])
        #         exit(1)
        #         pass
        #     continue
        
        # while True:
        #     new_node_mapping = node_mapping[node_mapping]
        #     print((new_node_mapping == node_mapping).sum(), 
        #     if np.all(new_node_mapping == node_mapping):
        #         break
        #     node_mapping = new_node_mapping
        #     continue
        
        new_node_mapping = np.full(node_mapping.shape, fill_value=-1, dtype=node_mapping.dtype)
        new_node_index = 0
        for ori_node, node in enumerate(node_mapping):
            if new_node_mapping[ori_node] != -1:
                continue
            instance = {ori_node: True}
            instance_index = -1
            while node not in instance:
                instance_index = new_node_mapping[node]
                if instance_index != -1:
                    break
                instance[node] = True
                node = node_mapping[node]
                continue
            instance = list(instance.keys())
            # if instance_index == 148 or new_node_index == 148:
            #     print([(_, new_node_mapping[_], node_mapping[_], instance_index, len(node_instances)) for _ in instance])
            #     pass
            if instance_index != -1:
                for node_index in instance:
                    new_node_mapping[node_index] = instance_index
                    continue
            else:
                for node_index in instance:
                    new_node_mapping[node_index] = new_node_index
                    continue
                new_node_index += 1                
                pass
            #print(node_instances)
            continue
        #node_mapping = new_node_mapping        
        ori_node_mapping = new_node_mapping[ori_node_mapping]
        
        intermediate_instances.append(ori_node_mapping)
        
        node_instances = [[] for _ in range(new_node_index)]
        for ori_node, node in enumerate(ori_node_mapping):
            node_instances[node].append(ori_node)
            continue
        
        # instance = (new_node_mapping == new_node_mapping[108277]).nonzero()[0]
        # print([(_, coords[_], toIndex(coords[_]) in instance_mask, new_node_mapping[_], node_mapping[_]) for _ in instance])        
        # for node, instance in enumerate(node_instances):
        #     mask = {}            
        #     for node_index in instance:
        #         mask[toIndex(coords[node_index]) in instance_mask] = node_index
        #         if len(mask) == 2:
        #             #node_mapping[_], new_node_mapping[_]
        #             print([(_, coords[_], toIndex(coords[_]) in instance_mask, new_node_mapping[_], node_mapping[_]) for _ in instance])
        #             print(node, mask)
        #             exit(1)
        #             pass
        #         continue
        #     continue
        
        # _, node_mapping = np.unique(node_mapping, return_inverse=True)
        # node_instances = [[] for _ in range(node_mapping.max() + 1)]        
        # for ori_node, node in enumerate(node_mapping):
        #     node_instances[node].append(ori_node)
        #     continue
        
        #print('num nodes', len(node_instances), max([len(instance) for instance in node_instances]), len(np.unique(np.concatenate([np.array(instance) for instance in node_instances], axis=0))), len(coords))
        
        iteration += 1        
        # if iteration == 5:
        #     break
        #if len(node_instances) < 100:
        #break

        if print_info:
            print('num nodes', len(node_instances))
            pass
        node_instances = [np.array(instance) for instance in node_instances]
        node_info = []
        for instance in node_instances:
            info = {}
            node_coords = coords[instance]
            labels = semantics[instance]
            unique_labels, counts = np.unique(labels, return_counts=True)
            label_counts = np.zeros(41)
            label_counts[unique_labels] = counts
            #print(instance, np.array([coord_node_map[0][toIndex(coord, full_scale)] for coord in node_coords]))
            #print('valid', np.all(neighbors[0][0][np.array([coord_node_map[0][toIndex(coord, full_scale)] for coord in node_coords])] == neighbors[0][0][instance]))
            #exit(1)
            info[0] = (node_coords, instance)
            for scale in range(1, num_scales):
                size = full_scale // pow(2, scale)
                node_coords = node_coords // 2
                indices = node_coords[:, 0] * size * size + node_coords[:, 1] * size + node_coords[:, 2]
                indices, mapping, counts = np.unique(indices, return_index=True, return_counts=True)
                valid_coords = []
                for index, coord_index, count in zip(indices, mapping, counts):
                    #if count >= count_dicts[scale][index] * 0.5:
                    if count >= scale_count_thresholds[scale]:
                        valid_coords.append(node_coords[coord_index])
                        pass
                    continue
                if len(valid_coords) > 0:
                    info[scale] = (valid_coords, np.array([coord_node_map[scale][toIndex(coord, full_scale // pow(2, scale))] for coord in valid_coords]))
                    pass
                pass
            node_info.append((info, label_counts))
            continue
        continue
    instances = ori_node_mapping

    np.save('cache/' + str(num_scales) + '/' + scene_id + '.npy', instances)
    return instances, intermediate_instances
    
    instance_labels, counts = np.unique(instances, return_counts=True)
    valid_labels = instance_labels[counts > 100]
    print('num valid instances', len(valid_labels))
    label_map = np.full(len(node_info), fill_value=-1, dtype=np.int32)
    for index, label in enumerate(valid_labels):
        label_map[label] = index
        continue
    instances = label_map[instances]
    # while True:
    #     new_instances = instances[instances]
    #     if np.all(new_instances == instances):
    #         break
    #     instances = new_instances
    #     continue    
    # _, instances = np.unique(instances, return_inverse=True)
    
    # if use_cache in [0, 1]:
    #     np.save('test/instance.npy', instances)
    #     pass
    return instances

# def findInstancesDebug(options, faces, semantics, instance_gt):
#     #print(faces.shape, faces.min(), faces.max(), semantics.shape)
#     edges = np.concatenate([faces[:, [0, 1]], faces[:, [0, 2]], faces[:, [1, 2]]], axis=0)
#     #print(len(instance_gt), faces.min(), faces.max(), edges.shape)
#     #scores = instance_gt[edges[:, 0]] == instance_gt[edges[:, 1]]
#     scores = semantics[edges[:, 0]] == semantics[edges[:, 1]]
#     #nodes = np.stack([np.arange(len(semantics), dtype=np.int32), np.arange(len(semantics))], axis=-1).tolist()
#     nodes = [[[node_index, ], node_index] for node_index in range(len(semantics))]
#     edges = np.concatenate([1 - np.expand_dims(scores, -1), edges], axis=-1)
#     #print((scores > 0.5).sum(), len(scores))
#     edge_queue = []    
#     for edge in edges:
#         edge_queue.append(tuple(edge))
#         #nodes[edge[1]][1].append(edge[2])
#         #nodes[edge[2]][1].append(edge[1])
#         continue
#     heapq.heapify(edge_queue)
#     threshold = 0.5
#     while True:
#         if len(edge_queue) == 0:
#             break
#         if len(edge_queue) % 1000 == 0:
#             print(len(edge_queue))
#             pass
#         edge = heapq.heappop(edge_queue)
#         if edge[0] > threshold:
#             break
#         node_indices = []
#         for node_index in edge[1:3]:
#             visited_node_indices = []
#             while nodes[node_index][-1] != node_index:
#                 visited_node_indices.append(node_index)                    
#                 node_index = nodes[node_index][-1]
#                 continue
#             for _ in visited_node_indices:
#                 nodes[_][-1] = node_index
#                 continue
#             node_indices.append(node_index)
#             continue
#         if node_indices[0] == node_indices[1]:
#             continue
#         nodes[node_indices[0]][0] += nodes[node_indices[1]][0]
#         nodes[node_indices[1]][0] = []
#         nodes[node_indices[1]][-1] = node_indices[0]
#         continue
#     instances = np.array([node[-1] for node in nodes])
#     while True:
#         new_instances = instances[instances]
#         if np.all(new_instances == instances):
#             break
#         instances = new_instances
#         continue
#     _, instances = np.unique(instances, return_inverse=True)
#     print('valid', (instances[edges[:, 0]] == instances[edges[:, 1]]).min())
#     return instances.astype(np.int64)
