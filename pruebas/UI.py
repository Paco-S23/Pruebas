# -------------------------------
# 4. UI: BARRA LATERAL (EL CHAT INTELIGENTE)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("Multi-Agent System Active")
    st.markdown("---")
    
    st.subheader("📂 Cargar Contrato Real")
    # WIDGET PARA SUBIR ARCHIVO
    uploaded_file = st.file_uploader("Sube tu contrato (.txt)", type=["txt"])
    
    contract_text = ""
    selected_contract_name = ""

    if uploaded_file is not None:
        # CASO 1: El usuario subió un archivo
        # Leemos el archivo y lo convertimos a string
        contract_text = uploaded_file.getvalue().decode("utf-8")
        selected_contract_name = uploaded_file.name
        st.success(f"✅ Archivo cargado: {selected_contract_name}")
    else:
        # CASO 2: No hay archivo, usamos la Base de Datos de Ejemplo
        st.info("ℹ️ Modo Demo (Usa el desplegable)")
        selected_contract_name = st.selectbox(
            "Selecciona un contrato de ejemplo:",
            options=list(contracts_db.keys())
        )
        contract_text = contracts_db[selected_contract_name]
    
    st.markdown("---")
    
    # B. INTERFAZ DE CHAT
    col_t, col_b = st.columns([2,1])
    with col_t: st.subheader("🤖 Agent Chat")
    with col_b: 
        if st.button("🗑️ Clear"): 
            st.session_state.messages = []
            st.rerun()
            
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "agent_used" in msg:
                    st.caption(f"Processed by: {msg['agent_used']}")

    # C. INPUT Y LÓGICA
    if prompt := st.chat_input("Pregunta sobre el contrato o busca noticias..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Pasamos bool(contract_text) para saber si hay contexto (sea subido o de ejemplo)
        decision = main_agent_router(prompt, bool(contract_text))
        
        final_response = ""
        agent_name = ""

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Orchestrator is routing to {decision}..."):
                    
                    if decision == "SEARCH_AGENT":
                        agent_name = "🌐 Search Agent"
                        raw_news = agent_web_searcher(prompt)
                        final_response = call_ibm_llm(f"Summarize these news for the user: {raw_news}")
                        
                    elif decision == "DOC_AGENT":
                        agent_name = "📄 Document Agent"
                        # Aquí se envía el texto del contrato (sea el subido o el de ejemplo)
                        final_response = agent_document_reader(prompt, contract_text)
                        
                    else:
                        agent_name = "🤖 General Assistant"
                        final_response = call_ibm_llm(f"Answer helpfuly: {prompt}")

                    st.markdown(final_response)
                    st.caption(f"⚡ Action handled by: {agent_name}")
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_response,
                        "agent_used": agent_name
                    })
