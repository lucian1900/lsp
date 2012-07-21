(defmacro defn (name args body)
    `(def ~name
        (fn (~@args) ~body)))