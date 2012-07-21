(defmacro defn (name args body)
  `(def ~name (fn (~@args) ~body)))

(defn inc (x) (+ x 1))

(defn dec (x) (- x 1))

(defn first (coll)
  (coll 0))

(defn second (coll)
  (coll 1))

(defn reduce (fun acc coll)
  (if (empty? coll)
    acc
    (reduce fun (fun acc (first coll)) (rest coll))))

(defn map (fun coll)
  (reduce (fn (acc e) (concat acc `(~(fun e)))) '() coll))

(defmacro let (pairs exp)
  `((fn (~@(slice pairs 0 (len pairs) 2)) ~exp)
    ~@(slice pairs 1 (len pairs) 2)))