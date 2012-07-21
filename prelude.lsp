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


(defn let (pairs exp)
  (`(fn () ~exp)))

