import time
from .greedy_coloring import greedy_graph_coloring
from .fpt_random_walk_coloring import fpt_random_walk_coloring_enhanced
from .dp_coloring import dp_branch_and_bound_coloring

def compare_algorithms(graph, num_registers=4, verbose=True, include_dp=True):
    """Compare greedy, FPT random walk, and DP coloring algorithms.
    
    Returns:
        dict: Comparison results with metrics for all algorithms
    """
    results = {
        "greedy": {},
        "fpt_random_walk": {},
        "dp": {},
    }
    
    # Run Greedy Algorithm
    start_time = time.perf_counter()
    greedy_assignment, greedy_spills = greedy_graph_coloring(graph, num_registers)
    greedy_time = time.perf_counter() - start_time
    
    results["greedy"] = {
        "assignment": greedy_assignment,
        "spills": greedy_spills,
        "num_spills": len(greedy_spills),
        "num_colored": len(greedy_assignment),
        "colors_used": len(set(greedy_assignment.values())),
        "time_seconds": greedy_time,
    }
    
    # Run FPT Random Walk Algorithm
    start_time = time.perf_counter()
    fpt_assignment, fpt_spills = fpt_random_walk_coloring_enhanced(
        graph,
        num_registers,
        num_iterations=8,
        fast_mode=True,
        max_extra_spills=1,
    )
    fpt_time = time.perf_counter() - start_time
    
    results["fpt_random_walk"] = {
        "assignment": fpt_assignment,
        "spills": fpt_spills,
        "num_spills": len(fpt_spills),
        "num_colored": len(fpt_assignment),
        "colors_used": len(set(fpt_assignment.values())) if fpt_assignment else 0,
        "time_seconds": fpt_time,
    }
    
    # Run DP Branch-and-Bound Algorithm
    if include_dp:
        start_time = time.perf_counter()
        dp_assignment, dp_spills = dp_branch_and_bound_coloring(graph, num_registers)
        dp_time = time.perf_counter() - start_time
        
        results["dp"] = {
            "assignment": dp_assignment,
            "spills": dp_spills,
            "num_spills": len(dp_spills),
            "num_colored": len(dp_assignment),
            "colors_used": len(set(dp_assignment.values())) if dp_assignment else 0,
            "time_seconds": dp_time,
        }
    
    if verbose:
        print("\n" + "=" * 90)
        print("ALGORITHM COMPARISON RESULTS")
        print("=" * 90)
        
        print(f"\nGraph Statistics:")
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        print(f"  Max Degree: {max(dict(graph.degree()).values()) if graph.number_of_nodes() > 0 else 0}")
        print(f"  Available Registers: {num_registers}")
        
        if include_dp:
            print(f"\n{'Metric':<25} {'Greedy':<20} {'FPT Random Walk':<20} {'DP B&B':<20}")
            print("-" * 90)
            
            print(f"{'Time (seconds)':<25} {greedy_time:<20.6f} {fpt_time:<20.6f} {results['dp']['time_seconds']:<20.6f}")
            print(f"{'Nodes Colored':<25} {results['greedy']['num_colored']:<20} {results['fpt_random_walk']['num_colored']:<20} {results['dp']['num_colored']:<20}")
            print(f"{'Spills':<25} {results['greedy']['num_spills']:<20} {results['fpt_random_walk']['num_spills']:<20} {results['dp']['num_spills']:<20}")
            print(f"{'Colors Used':<25} {results['greedy']['colors_used']:<20} {results['fpt_random_walk']['colors_used']:<20} {results['dp']['colors_used']:<20}")
            
            # Quality score (higher is better)
            greedy_quality = max(0, results['greedy']['num_colored'] - results['greedy']['num_spills'] * 2)
            fpt_quality = max(0, results['fpt_random_walk']['num_colored'] - results['fpt_random_walk']['num_spills'] * 2)
            dp_quality = max(0, results['dp']['num_colored'] - results['dp']['num_spills'] * 2)
            
            print(f"{'Quality Score':<25} {greedy_quality:<20} {fpt_quality:<20} {dp_quality:<20}")
            
            # Determine best result
            scores = {
                "Greedy": greedy_quality,
                "FPT Random Walk": fpt_quality,
                "DP B&B": dp_quality,
            }
            best_method = max(scores, key=scores.get)
            
            print("\n" + "-" * 90)
            print(f"BEST RESULT: {best_method} Algorithm")
            if scores[best_method] == greedy_quality and best_method == "Greedy":
                print("Reason: Best quality coloring with fastest execution time")
            else:
                print(f"Reason: Best quality score ({scores[best_method]} points)")
            print("=" * 90 + "\n")
        else:
            print(f"\n{'Metric':<30} {'Greedy':<20} {'FPT Random Walk':<20}")
            print("-" * 70)
            
            print(f"{'Time (seconds)':<30} {greedy_time:<20.6f} {fpt_time:<20.6f}")
            print(f"{'Nodes Colored':<30} {results['greedy']['num_colored']:<20} {results['fpt_random_walk']['num_colored']:<20}")
            print(f"{'Spills':<30} {results['greedy']['num_spills']:<20} {results['fpt_random_walk']['num_spills']:<20}")
            print(f"{'Colors Used':<30} {results['greedy']['colors_used']:<20} {results['fpt_random_walk']['colors_used']:<20}")
            
            greedy_quality = max(0, results['greedy']['num_colored'] - results['greedy']['num_spills'] * 2)
            fpt_quality = max(0, results['fpt_random_walk']['num_colored'] - results['fpt_random_walk']['num_spills'] * 2)
            
            print(f"{'Quality Score':<30} {greedy_quality:<20} {fpt_quality:<20}")
            
            # Determine best result
            greedy_wins = (
                (results['greedy']['num_spills'] < results['fpt_random_walk']['num_spills']) +
                (greedy_time < fpt_time) +
                (greedy_quality > fpt_quality)
            )
            
            print("\n" + "-" * 70)
            if greedy_wins >= 2:
                print("BEST RESULT: Greedy Algorithm")
                print("Reason: Better overall performance on this instance")
            elif greedy_wins == 0:
                print("BEST RESULT: FPT Random Walk Algorithm")
                print("Reason: Better quality coloring with fewer spills")
            else:
                print("RESULT: Trade-off between algorithms")
                print("Reason: Different strengths on different metrics")
            
            print("=" * 70 + "\n")
    
    return results
