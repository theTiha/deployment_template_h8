import lib.KubernetesSDK as k8s_sdk   

if __name__ == "__main__":
    # Master Node init and setup cillium 
    k8s = k8s_sdk.Kubernetes()
    # k8s.kubeadm_init()
    # k8s.add_kube_config()
    # k8s.setup_cillium_cp()
    
    # # # Worker Node join and wait 
    # wn_host = k8s.identify_wnodes_role()
    # cp_host = k8s.identify_controller_role()
    # token = k8s.get_join_command(host=cp_host) 
    # k8s.join_controller(join_command=token)
    # k8s.wait_for_nodes_ready(node_hostnames=wn_host)
    
    # MetalLB install and setup
    # k8s.install_metallb()
    # k8s.wait_for_metallb_ready()
    # k8s.configure_metallb()
    
    # Github deployment
    #k8s.clone_and_apply_kubectl_commands()
    k8s.execute_tasks()

