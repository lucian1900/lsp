(defmacro defn (name args body)
  `(def ~name (fn (~@args) ~body)))

(defn inc (x) (+ x 1))

(defn dec (x) (- x 1))